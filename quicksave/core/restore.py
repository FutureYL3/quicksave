import os
import pathlib
import shutil
import signal
import subprocess
import tempfile
from typing import List

from quicksave.utils.logger import log
from quicksave.utils.timer import timed
from quicksave.utils.compress import decompress_file
from ._criu import build as criu_cmd

__all__ = ["restore", "verify_only"]

_PIDFILE = "restored.pid"


def _exec(cmd: List[str]) -> bool:
    """运行 cmd；Ctrl-C 时杀掉整个进程组并返回 False。"""
    log.debug("exec %s", " ".join(cmd))
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,     # 屏蔽 “Session terminated…” 噪音
        preexec_fn=os.setsid           # 让其成为新进程组组长
    )
    try:
        return proc.wait() == 0
    except KeyboardInterrupt:
        log.warning("KeyboardInterrupt → killing restore group ...")
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        proc.wait()
        return False                   # **不再 raise**，而是返回失败



def _do_restore(workdir: pathlib.Path) -> bool:
    """
    root   : script -q -c "<criu restore ...>" /dev/null
             （保持输出，Ctrl-C 可终止）
    non-root: criu restore（rootless 仅限无 TTY 应用）
    """
    base = criu_cmd(
    "restore", "-D", str(workdir),
    "--shell-job", "--tcp-established", "--ext-unix-sk", "--pty"
    )

    # ➜ 用 script 创建 pty；恢复完成后立刻:
    #    1) 切回备用屏    (printf '\e[?1049h')
    #    2) 触发 Ctrl-L   (printf '\f')
    cmd = [
        "script", "-q", "-c",
        " ".join([
            *base,
            "&&", "printf", "'\\033[?1049h\\f'"
        ]),
        "/dev/null"
    ] 

    return _exec(cmd)


@timed
def verify_only(qsnap: pathlib.Path) -> bool:
    """
    后台恢复→读取 pidfile→立刻 kill；快速验证镜像完整性。
    """
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="qs_ver_"))
    pidfile = tmp / _PIDFILE
    try:
        decompress_file(qsnap, tmp)
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

        log.info("verify %s => %s", qsnap.name, ok)
        return ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@timed
def restore(qsnap: pathlib.Path) -> bool:
    """
    解压 .qsnap → restore；成功则删除 .bak，否则回滚。
    root 场景下 loop 输出直接续写当前终端，
    Ctrl-C 可安全终止恢复与被恢复进程。
    """
    if not qsnap.exists():
        raise FileNotFoundError(qsnap)

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="qs_res_"))
    bak = qsnap.with_suffix(".bak")
    ok = False
    try:
        decompress_file(qsnap, tmp)
        qsnap.rename(bak)
        ok = _do_restore(tmp)
        if ok:
            bak.unlink()
        else:
            bak.rename(qsnap)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return ok