"""
主程序入口，启动 GUI 和守护进程。
"""
import pathlib
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from .tray_icon import TrayIcon
from ..daemon import ProcessMonitor, SnapshotScheduler
from ..utils.logger import log

CONFIG_FILE = pathlib.Path.home() / ".quicksave" / "config.json"

def main():
    """启动应用程序"""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    # 创建托盘图标
    tray = TrayIcon()
    tray.show()
    
    # 启动守护进程
    monitor = ProcessMonitor(CONFIG_FILE)
    scheduler = SnapshotScheduler(CONFIG_FILE)
    
    monitor.start()
    scheduler.start()
    
    # 注册退出处理
    def cleanup():
        log.info("正在退出...")
        monitor.stop()
        scheduler.stop()
        monitor.join()
        scheduler.join()
    
    app.aboutToQuit.connect(cleanup)
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main()) 