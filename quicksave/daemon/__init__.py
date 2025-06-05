"""
quicksave.daemon
~~~~~~~~~~~~~~
提供后台守护进程功能，包括自动快照和进程监控。
"""

from .monitor import ProcessMonitor
from .scheduler import SnapshotScheduler

__all__ = ["ProcessMonitor", "SnapshotScheduler"] 