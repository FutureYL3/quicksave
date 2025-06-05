import os
import pathlib
import shutil
import signal
import subprocess
import tempfile
import sys
from typing import List

from quicksave.utils.logger import log
from quicksave.utils.timer import timed
from quicksave.utils.compress import decompress_file
from ._criu import build as criu_cmd

__all__ = ["restore", "verify_only"]

_PIDFILE = "restored.pid"


def _fix_permissions(directory: pathlib.Path):
    """修复目录中所有文件的权限"""
    try:
        log.info("开始修复文件权限...")
        for root, dirs, files in os.walk(directory):
            # 修复目录权限
            for d in dirs:
                path = pathlib.Path(root) / d
                try:
                    os.chmod(path, 0o755)  # drwxr-xr-x
                    log.debug("修复目录权限: %s", path)
                except Exception as e:
                    log.warning("修复目录权限失败 %s: %s", path, e)
            
            # 修复文件权限
            for f in files:
                path = pathlib.Path(root) / f
                try:
                    # 检查文件是否可执行
                    if os.access(path, os.X_OK):
                        os.chmod(path, 0o755)  # -rwxr-xr-x
                    else:
                        os.chmod(path, 0o644)  # -rw-r--r--
                    log.debug("修复文件权限: %s", path)
                except Exception as e:
                    log.warning("修复文件权限失败 %s: %s", path, e)
        log.info("文件权限修复完成")
    except Exception as e:
        log.error("修复文件权限时发生错误: %s", e)


def _exec(cmd: List[str]) -> bool:
    """运行 cmd；Ctrl-C 时杀掉整个进程组并返回 False。"""
    log.debug("执行命令: %s", " ".join(cmd))
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stderr=subprocess.PIPE,     # 捕获错误输出
        stdout=subprocess.PIPE,     # 捕获标准输出
        preexec_fn=os.setsid        # 让其成为新进程组组长
    )
    try:
        stdout, stderr = proc.communicate()
        if stdout:
            log.info("命令输出: %s", stdout.decode('utf-8', errors='ignore'))
        if stderr:
            log.error("命令错误: %s", stderr.decode('utf-8', errors='ignore'))
        return proc.returncode == 0
    except KeyboardInterrupt:
        log.warning("收到中断信号，正在终止恢复进程组...")
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        proc.wait()
        return False


def _do_restore(workdir: pathlib.Path) -> bool:
    """
    执行恢复操作。
    在终端中执行恢复命令。
    """
    try:
        # 修复文件权限
        _fix_permissions(workdir)
        
        # 获取 Python 解释器路径
        python_exe = sys.executable
        
        # 获取原始快照文件路径
        original_snapshot = workdir.parent / f"{workdir.name}.qsnap"
        if not original_snapshot.exists():
            original_snapshot = workdir.parent / f"{workdir.name}.bak"
        
        # 构建恢复命令
        restore_cmd = f'"{python_exe}" -m quicksave.core.cli restore "{original_snapshot}"'
        log.info("构建恢复命令: %s", restore_cmd)
        
        # 根据操作系统选择终端命令
        if os.name == 'nt':  # Windows
            # 使用 PowerShell 创建新窗口并执行命令
            cmd = [
                "powershell", "-NoProfile", "-Command",
                f'Start-Process powershell -ArgumentList "-NoProfile -Command \\"{restore_cmd}; Write-Host \\"按任意键关闭窗口...\\"; $null = $Host.UI.RawUI.ReadKey(\\"NoEcho,IncludeKeyDown\\")\\"" -Verb RunAs -Wait'
            ]
        else:  # Linux/Unix
            # 使用 gnome-terminal 或其他终端模拟器
            terminal_cmd = 'gnome-terminal' if os.path.exists('/usr/bin/gnome-terminal') else 'x-terminal-emulator'
            # 构建完整的命令，包括错误处理和用户提示
            full_cmd = f"""
echo "开始恢复快照..."
echo "执行命令: {restore_cmd}"
echo "----------------------------------------"
sudo {restore_cmd}
result=$?
echo "----------------------------------------"
if [ $result -eq 0 ]; then
    echo "恢复成功！"
else
    echo "恢复失败，错误代码: $result"
    echo "请检查以下可能的问题："
    echo "1. 确保有足够的权限执行恢复操作"
    echo "2. 检查快照文件是否完整"
    echo "3. 检查系统是否支持所需的 CRIU 功能"
    echo "4. 查看系统日志获取更多信息"
fi
echo "----------------------------------------"
echo "按回车键关闭窗口..."
read
"""
            cmd = [
                terminal_cmd, '--',
                'bash', '-c',
                full_cmd
            ]
        
        log.info("执行终端命令: %s", " ".join(cmd))
        result = _exec(cmd)
        
        return result
    except Exception as e:
        log.error("恢复操作失败: %s", str(e))
        return False


@timed
def verify_only(qsnap: pathlib.Path) -> bool:
    """
    验证快照完整性。
    后台恢复→读取 pidfile→立刻 kill；快速验证镜像完整性。
    """
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="qs_ver_"))
    pidfile = tmp / _PIDFILE
    try:
        log.info("开始验证快照: %s", qsnap)
        decompress_file(qsnap, tmp)
        
        # 修复文件权限
        _fix_permissions(tmp)
        
        base = criu_cmd(
            "restore", "-D", str(tmp),
            "--shell-job", "--ext-unix-sk", "-d",
            "--pidfile", str(pidfile)
        )
        cmd = (["script", "-q", "-c", " ".join(base), "/dev/null"]
               if os.geteuid() == 0 else base)

        ok = _exec(cmd)

        if ok and pidfile.exists():
            pid = int(pidfile.read_text().strip())
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

        log.info("验证结果: %s => %s", qsnap.name, ok)
        return ok
    except Exception as e:
        log.error("验证快照失败: %s", str(e))
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@timed
def restore(qsnap: pathlib.Path) -> bool:
    """
    恢复快照。
    解压 .qsnap → restore；成功则删除 .bak，否则回滚。
    """
    if not qsnap.exists():
        log.error("快照文件不存在: %s", qsnap)
        raise FileNotFoundError(qsnap)

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="qs_res_"))
    bak = qsnap.with_suffix(".bak")
    ok = False
    
    try:
        log.info("开始恢复快照: %s", qsnap)
        decompress_file(qsnap, tmp)
        qsnap.rename(bak)
        
        # 检查解压后的文件
        log.info("检查解压后的文件...")
        for root, dirs, files in os.walk(tmp):
            for f in files:
                path = pathlib.Path(root) / f
                log.debug("文件: %s (大小: %d 字节)", path, path.stat().st_size)
        
        # 在终端中执行恢复命令
        ok = _do_restore(tmp)
        if ok:
            log.info("恢复成功，删除备份文件")
            bak.unlink()
        else:
            log.warning("恢复失败，回滚到原始快照")
            bak.rename(qsnap)
            
        return ok
    except Exception as e:
        log.error("恢复快照时发生错误: %s", str(e))
        if bak.exists():
            log.info("回滚到原始快照")
            bak.rename(qsnap)
        return False
    finally:
        # 保存日志文件
        log_dir = pathlib.Path.home() / ".quicksave" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        try:
            if (tmp / "restore.log").exists():
                shutil.copy2(tmp / "restore.log", log_dir / f"restore_{qsnap.stem}.log")
            if (tmp / "action.log").exists():
                shutil.copy2(tmp / "action.log", log_dir / f"action_{qsnap.stem}.log")
        except Exception as e:
            log.error("保存日志文件失败: %s", e)
        
        shutil.rmtree(tmp, ignore_errors=True)
