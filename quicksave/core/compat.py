import os

def _check_x11(pid: int) -> bool:
    try:
        with open(f"/proc/{pid}/environ", "rb") as f:
            env = f.read().split(b'\0')
            for item in env:
                if item.startswith(b'DISPLAY='):
                    return True
    except Exception:
        pass
    return False

def _check_wayland(pid: int) -> bool:
    try:
        with open(f"/proc/{pid}/environ", "rb") as f:
            env = f.read().split(b'\0')
            for item in env:
                if item.startswith(b'WAYLAND_DISPLAY'):
                    return True
    except Exception:
        pass
    return False

def _check_gpu(pid: int) -> bool:
    """检测是否依赖 GPU 设备"""
    try:
        for fd in os.listdir(f"/proc/{pid}/fd"):
            try:
                target = os.readlink(f"/proc/{pid}/fd/{fd}")
                if "dri" in target or "nvidia" in target:
                    return True
            except:
                continue
    except Exception:
        pass
    return False

def _check_ipc(pid: int) -> int:
    """返回 socket fd 数"""
    count = 0
    try:
        for fd in os.listdir(f"/proc/{pid}/fd"):
            try:
                target = os.readlink(f"/proc/{pid}/fd/{fd}")
                if "socket:" in target or "pipe:" in target:
                    count += 1
            except:
                continue
    except Exception:
        pass
    return count

def _check_cmdline(pid: int) -> str:
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().decode().replace('\x00', ' ')
    except Exception:
        return ""

def is_gui_blacklisted(cmdline: str) -> bool:
    # 典型不可恢复应用
    keywords = ["chrome", "firefox", "vscode", "pycharm", "idea", "jetbrains"]
    return any(k in cmdline.lower() for k in keywords)

def check_compatibility(pids):
    """
    对一组进程（含子进程）综合评估兼容性，输出结构化检测报告
    """
    report = {"x11": False, "wayland": False, "gpu": False,
              "ipc": 0, "blacklist": False, "cmdlines": []}
    for pid in pids:
        if _check_x11(pid):
            report["x11"] = True
        if _check_wayland(pid):
            report["wayland"] = True
        if _check_gpu(pid):
            report["gpu"] = True
        report["ipc"] += _check_ipc(pid)
        cmd = _check_cmdline(pid)
        report["cmdlines"].append(cmd)
        if is_gui_blacklisted(cmd):
            report["blacklist"] = True
    return report

def explain_compat(report) -> str:
    if report["wayland"]:
        return "当前应用运行于 Wayland，不支持进程快照。"
    if report["blacklist"]:
        return "检测到典型不可快照的应用（如 Chrome/VSCode/PyCharm）。"
    if report["gpu"]:
        return "检测到该应用正在使用 GPU，快照/恢复可能失败。"
    if not report["x11"]:
        return "未检测到 X11 环境，无法快照窗口应用。"
    if report["ipc"] > 30:
        return f"进程间 socket/pipe 数量较多（{report['ipc']}），快照兼容性风险较高。"
    return "兼容性检测通过，可以尝试快照。"