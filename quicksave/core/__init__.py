"""
quicksave.core
~~~~~~~~~~~~~~
封装 CRIU 快照/恢复原语，供 GUI 与守护进程调用。
"""
from importlib.metadata import version, PackageNotFoundError

try:               # 允许 pip install -e 本地测试
    __version__ = version("quicksave")
except PackageNotFoundError:
    __version__ = "0.0.dev0"

from .snapshot import dump
from .restore  import restore, verify_only

__all__ = ["dump", "restore", "verify_only"]