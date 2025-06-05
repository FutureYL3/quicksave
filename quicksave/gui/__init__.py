"""
quicksave.gui
~~~~~~~~~~~~~~
提供 PyQt 图形界面，包括托盘图标、快照管理和设置面板。
"""

from .main_window import MainWindow
from .tray_icon import TrayIcon
from .settings import SettingsDialog
from .snapshot_list import SnapshotListWidget

__all__ = ["MainWindow", "TrayIcon", "SettingsDialog", "SnapshotListWidget"] 