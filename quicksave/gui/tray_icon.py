"""
托盘图标组件，提供系统托盘功能和快速操作。
"""
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt

from .main_window import MainWindow
from .settings import SettingsDialog
from ..utils.logger import log

class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = MainWindow()
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        # 设置图标
        self.setIcon(QIcon.fromTheme("system-save"))
        self.setToolTip("QuickSave")
        
        # 创建菜单
        menu = QMenu()
        
        # 显示主窗口
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show_main_window)
        menu.addAction(show_action)
        
        # 创建快照
        snapshot_action = QAction("创建快照", self)
        snapshot_action.triggered.connect(self.create_snapshot)
        menu.addAction(snapshot_action)
        
        menu.addSeparator()
        
        # 设置
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        # 退出
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)
        
        self.setContextMenu(menu)
        
        # 连接信号
        self.activated.connect(self.on_activated)
    
    def show_main_window(self):
        """显示主窗口"""
        self.main_window.show()
        self.main_window.activateWindow()
    
    def create_snapshot(self):
        """创建快照"""
        try:
            # TODO: 实现进程选择对话框
            pids = [1234]  # 示例 PID
            from ..core import dump
            snapshot_path = dump(pids)
            self.showMessage(
                "QuickSave",
                f"已创建快照: {snapshot_path.name}",
                QSystemTrayIcon.MessageIcon.Information,
                3000
            )
        except Exception as e:
            log.error("创建快照失败: %s", e)
            self.showMessage(
                "QuickSave",
                f"创建快照失败: {str(e)}",
                QSystemTrayIcon.MessageIcon.Critical,
                5000
            )
    
    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.main_window)
        dialog.exec()
    
    def quit_app(self):
        """退出应用"""
        self.main_window.close()
        self.hide()
    
    def on_activated(self, reason):
        """处理托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_main_window() 