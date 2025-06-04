"""
构造适合当前权限的 CRIU 命令行。
非 root 时自动插入 --unprivileged，并去掉需要特权的选项。
"""
import os
from typing import List

_ROOT_ONLY = {"--tcp-established", "--track-mem"}

def build(*args: str) -> List[str]:
    cmd: List[str] = ["criu", *args]
    if os.geteuid() != 0:
        if "--unprivileged" not in cmd:
            cmd.insert(1, "--unprivileged")
        cmd = [str(a) for a in cmd if a not in _ROOT_ONLY]
    else:
        cmd = [str(a) for a in cmd]
    return cmd