"""
主窗口实现，包含进程列表、快照列表和基本操作按钮。
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QTabWidget
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon
import psutil
import subprocess
import os
import sys
import logging
import pathlib

from .snapshot_list import SnapshotListWidget
from .settings import SettingsDialog
from ..core import dump, restore
from ..utils.logger import log

# 配置日志
LOG_DIR = pathlib.Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "quicksave.log"

# 创建日志处理器
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
log.addHandler(file_handler)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuickSave")
        self.setMinimumSize(1000, 700)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # 进程列表页面
        process_widget = QWidget()
        process_layout = QVBoxLayout(process_widget)
        
        # 进程搜索栏
        search_layout = QHBoxLayout()
        self.process_search = QLineEdit()
        self.process_search.setPlaceholderText("搜索进程...")
        self.process_search.textChanged.connect(self.filter_processes)
        search_layout.addWidget(self.process_search)
        process_layout.addLayout(search_layout)
        
        # 进程表格
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(4)
        self.process_table.setHorizontalHeaderLabels(["选择", "PID", "进程名", "内存使用"])
        self.process_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.process_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.process_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        process_layout.addWidget(self.process_table)
        
        # 进程操作按钮
        process_btn_layout = QHBoxLayout()
        
        self.refresh_process_btn = QPushButton("刷新进程列表")
        self.refresh_process_btn.clicked.connect(self.refresh_processes)
        process_btn_layout.addWidget(self.refresh_process_btn)
        
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all_processes)
        process_btn_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton("取消全选")
        self.deselect_all_btn.clicked.connect(self.deselect_all_processes)
        process_btn_layout.addWidget(self.deselect_all_btn)
        
        self.create_snapshot_btn = QPushButton("为选中进程创建快照")
        self.create_snapshot_btn.clicked.connect(self.create_snapshot)
        process_btn_layout.addWidget(self.create_snapshot_btn)
        
        process_layout.addLayout(process_btn_layout)
        
        # 快照列表页面
        snapshot_widget = QWidget()
        snapshot_layout = QVBoxLayout(snapshot_widget)
        
        # 快照搜索栏
        snapshot_search_layout = QHBoxLayout()
        self.snapshot_search = QLineEdit()
        self.snapshot_search.setPlaceholderText("搜索快照...")
        self.snapshot_search.textChanged.connect(self.filter_snapshots)
        snapshot_search_layout.addWidget(self.snapshot_search)
        snapshot_layout.addLayout(snapshot_search_layout)
        
        # 快照列表
        self.snapshot_list = SnapshotListWidget(self)
        self.snapshot_list.restore_requested.connect(self.restore_snapshot)
        self.snapshot_list.delete_requested.connect(self.delete_snapshot)
        snapshot_layout.addWidget(self.snapshot_list)
        
        # 快照操作按钮
        snapshot_btn_layout = QHBoxLayout()
        
        self.refresh_snapshot_btn = QPushButton("刷新快照列表")
        self.refresh_snapshot_btn.clicked.connect(self.refresh_snapshots)
        snapshot_btn_layout.addWidget(self.refresh_snapshot_btn)
        
        self.restore_btn = QPushButton("恢复选中")
        self.restore_btn.clicked.connect(lambda: self.restore_snapshot(self.snapshot_list.get_selected()))
        snapshot_btn_layout.addWidget(self.restore_btn)
        
        self.settings_btn = QPushButton("设置")
        self.settings_btn.clicked.connect(self.show_settings)
        snapshot_btn_layout.addWidget(self.settings_btn)
        
        snapshot_layout.addLayout(snapshot_btn_layout)
        
        # 添加标签页
        self.tab_widget.addTab(process_widget, "进程列表")
        self.tab_widget.addTab(snapshot_widget, "快照列表")
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
        # 加载进程列表
        self.refresh_processes()
        # 加载快照列表
        self.refresh_snapshots()
    
    def refresh_processes(self):
        """刷新进程列表"""
        self.process_table.setRowCount(0)
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                row = self.process_table.rowCount()
                self.process_table.insertRow(row)
                
                # 添加复选框
                checkbox = QCheckBox()
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                self.process_table.setCellWidget(row, 0, checkbox_widget)
                
                # 添加进程信息
                self.process_table.setItem(row, 1, QTableWidgetItem(str(proc.info['pid'])))
                self.process_table.setItem(row, 2, QTableWidgetItem(proc.info['name']))
                memory_mb = proc.info['memory_info'].rss / (1024 * 1024)
                self.process_table.setItem(row, 3, QTableWidgetItem(f"{memory_mb:.1f} MB"))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        self.statusBar().showMessage("进程列表已刷新")
    
    def refresh_snapshots(self):
        """刷新快照列表"""
        self.snapshot_list.refresh()
        self.statusBar().showMessage("快照列表已刷新")
    
    def filter_processes(self, text):
        """根据搜索文本过滤进程列表"""
        for row in range(self.process_table.rowCount()):
            process_name = self.process_table.item(row, 2).text().lower()
            pid = self.process_table.item(row, 1).text()
            show = text.lower() in process_name or text in pid
            self.process_table.setRowHidden(row, not show)
    
    def select_all_processes(self):
        """选择所有进程"""
        for row in range(self.process_table.rowCount()):
            if not self.process_table.isRowHidden(row):
                checkbox_widget = self.process_table.cellWidget(row, 0)
                checkbox = checkbox_widget.findChild(QCheckBox)
                checkbox.setChecked(True)
    
    def deselect_all_processes(self):
        """取消选择所有进程"""
        for row in range(self.process_table.rowCount()):
            checkbox_widget = self.process_table.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            checkbox.setChecked(False)
    
    def get_selected_pids(self):
        """获取选中的进程PID列表"""
        selected_pids = []
        for row in range(self.process_table.rowCount()):
            checkbox_widget = self.process_table.cellWidget(row, 0)
            checkbox = checkbox_widget.findChild(QCheckBox)
            if checkbox.isChecked():
                pid = int(self.process_table.item(row, 1).text())
                selected_pids.append(pid)
        return selected_pids
    
    def create_snapshot(self):
        """创建新快照"""
        try:
            pids = self.get_selected_pids()
            if not pids:
                QMessageBox.warning(self, "警告", "请至少选择一个进程")
                return
                
            log.info("准备为进程创建快照: %s", pids)
            snapshot_path = dump(pids)
            self.refresh_snapshots()
            self.statusBar().showMessage(f"已创建快照: {snapshot_path.name}")
            log.info("快照创建成功: %s", snapshot_path)
            # 切换到快照列表标签页
            self.tab_widget.setCurrentIndex(1)
        except Exception as e:
            error_msg = f"创建快照失败: {str(e)}"
            log.error(error_msg)
            log.error("详细错误信息:", exc_info=True)
            QMessageBox.critical(self, "错误", error_msg)
    
    def filter_snapshots(self, text):
        """根据搜索文本过滤快照列表"""
        self.snapshot_list.filter(text)
    
    def restore_snapshot(self, snapshot_path):
        """恢复选中的快照"""
        if not snapshot_path:
            QMessageBox.warning(self, "警告", "请先选择要恢复的快照")
            return
        
        try:
            log.info("准备恢复快照: %s", snapshot_path)
            self.statusBar().showMessage("正在恢复快照...")
            
            # 直接调用 restore 函数
            if restore(snapshot_path):
                self.statusBar().showMessage("快照恢复成功")
                log.info("快照恢复成功")
                QMessageBox.information(self, "成功", 
                    "快照恢复成功！\n"
                    "如果恢复的进程没有正常启动，请检查日志文件获取详细信息。")
            else:
                error_msg = "快照恢复失败，请检查日志文件获取详细信息"
                log.error(error_msg)
                QMessageBox.warning(self, "警告", error_msg)
            
        except Exception as e:
            error_msg = f"恢复快照失败: {str(e)}"
            log.error(error_msg)
            log.error("详细错误信息:", exc_info=True)
            
            # 显示错误对话框
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("错误")
            msg_box.setText(error_msg)
            msg_box.setDetailedText(
                f"错误信息已记录到日志文件：\n{LOG_FILE}\n\n"
                f"请查看日志文件获取详细信息。"
            )
            msg_box.exec()
            
            self.statusBar().showMessage("快照恢复失败")
    
    def delete_snapshot(self, snapshot_path):
        """删除选中的快照"""
        if not snapshot_path:
            return
            
        try:
            log.info("准备删除快照: %s", snapshot_path)
            snapshot_path.unlink()
            self.refresh_snapshots()
            self.statusBar().showMessage("快照已删除")
            log.info("快照删除成功")
        except Exception as e:
            error_msg = f"删除快照失败: {str(e)}"
            log.error(error_msg)
            log.error("详细错误信息:", exc_info=True)
            QMessageBox.critical(self, "错误", error_msg)
    
    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self)
        dialog.exec() 