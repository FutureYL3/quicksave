"""
快照列表组件，显示快照信息并提供过滤功能。
"""
import pathlib
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QAction

from ..core import QS_DIR
from ..utils.logger import log

class SnapshotListWidget(QWidget):
    # 定义信号
    restore_requested = pyqtSignal(pathlib.Path)
    delete_requested = pyqtSignal(pathlib.Path)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["名称", "大小", "时间", "状态"])
        
        # 设置表格属性
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.table)
    
    def refresh(self):
        """刷新快照列表"""
        self.table.setRowCount(0)
        if not QS_DIR.exists():
            return
        
        for file in QS_DIR.glob("*.qsnap"):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # 文件名
            name_item = QTableWidgetItem(file.name)
            name_item.setData(Qt.ItemDataRole.UserRole, file)
            self.table.setItem(row, 0, name_item)
            
            # 文件大小
            size = file.stat().st_size
            size_str = f"{size / 1024 / 1024:.1f} MB"
            self.table.setItem(row, 1, QTableWidgetItem(size_str))
            
            # 修改时间
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            time_str = mtime.strftime("%Y-%m-%d %H:%M:%S")
            self.table.setItem(row, 2, QTableWidgetItem(time_str))
            
            # 状态
            self.table.setItem(row, 3, QTableWidgetItem("就绪"))
    
    def filter(self, text):
        """根据文本过滤快照列表"""
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            self.table.setRowHidden(row, text.lower() not in name_item.text().lower())
    
    def get_selected(self) -> pathlib.Path | None:
        """获取选中的快照文件路径"""
        selected = self.table.selectedItems()
        if not selected:
            return None
        return selected[0].data(Qt.ItemDataRole.UserRole)
    
    def show_context_menu(self, pos):
        """显示右键菜单"""
        selected = self.get_selected()
        if not selected:
            return
            
        menu = QMenu(self)
        
        restore_action = QAction("恢复", self)
        restore_action.triggered.connect(lambda: self.restore_requested.emit(selected))
        menu.addAction(restore_action)
        
        menu.addSeparator()
        
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_requested.emit(selected))
        menu.addAction(delete_action)
        
        menu.exec(self.table.mapToGlobal(pos))
    
    def delete_selected(self):
        """删除选中的快照"""
        selected = self.get_selected()
        if not selected:
            return
        
        try:
            selected.unlink()
            self.refresh()
            self.parent().statusBar().showMessage("快照已删除")
        except Exception as e:
            log.error("删除快照失败: %s", e) 