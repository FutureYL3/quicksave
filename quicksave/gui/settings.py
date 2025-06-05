"""
设置对话框，包含压缩算法、历史份数、黑白名单等设置。
"""
import json
import pathlib
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QSpinBox, QTextEdit, QPushButton,
    QTabWidget, QWidget, QMessageBox
)
from PyQt6.QtCore import Qt

from ..utils.compress import ALG_ZSTD, ALG_LZ4
from ..utils.logger import log

CONFIG_FILE = pathlib.Path.home() / ".quicksave" / "config.json"

DEFAULT_CONFIG = {
    "compression": "zstd" if ALG_ZSTD else "lz4",
    "max_history": 10,
    "whitelist": [],
    "blacklist": [],
    "auto_snapshot": {
        "enabled": False,
        "time": "22:00",
        "interval": 24,  # 小时
    }
}

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = self.load_config()
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("QuickSave 设置")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # 创建选项卡
        tabs = QTabWidget()
        
        # 基本设置
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # 压缩算法
        comp_layout = QHBoxLayout()
        comp_layout.addWidget(QLabel("压缩算法:"))
        self.comp_algo = QComboBox()
        if ALG_ZSTD:
            self.comp_algo.addItem("zstd")
        if ALG_LZ4:
            self.comp_algo.addItem("lz4")
        self.comp_algo.setCurrentText(self.config["compression"])
        comp_layout.addWidget(self.comp_algo)
        basic_layout.addLayout(comp_layout)
        
        # 历史份数
        history_layout = QHBoxLayout()
        history_layout.addWidget(QLabel("保留历史份数:"))
        self.max_history = QSpinBox()
        self.max_history.setRange(1, 100)
        self.max_history.setValue(self.config["max_history"])
        history_layout.addWidget(self.max_history)
        basic_layout.addLayout(history_layout)
        
        basic_layout.addStretch()
        tabs.addTab(basic_tab, "基本设置")
        
        # 进程过滤
        filter_tab = QWidget()
        filter_layout = QVBoxLayout(filter_tab)
        
        # 白名单
        filter_layout.addWidget(QLabel("白名单 (每行一个进程名):"))
        self.whitelist = QTextEdit()
        self.whitelist.setPlainText("\n".join(self.config["whitelist"]))
        filter_layout.addWidget(self.whitelist)
        
        # 黑名单
        filter_layout.addWidget(QLabel("黑名单 (每行一个进程名):"))
        self.blacklist = QTextEdit()
        self.blacklist.setPlainText("\n".join(self.config["blacklist"]))
        filter_layout.addWidget(self.blacklist)
        
        tabs.addTab(filter_tab, "进程过滤")
        
        # 自动快照
        auto_tab = QWidget()
        auto_layout = QVBoxLayout(auto_tab)
        
        # 启用自动快照
        self.auto_enabled = QComboBox()
        self.auto_enabled.addItems(["禁用", "启用"])
        self.auto_enabled.setCurrentIndex(1 if self.config["auto_snapshot"]["enabled"] else 0)
        auto_layout.addWidget(QLabel("自动快照:"))
        auto_layout.addWidget(self.auto_enabled)
        
        # 快照时间
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("快照时间:"))
        self.snapshot_time = QComboBox()
        for hour in range(24):
            self.snapshot_time.addItem(f"{hour:02d}:00")
        self.snapshot_time.setCurrentText(self.config["auto_snapshot"]["time"])
        time_layout.addWidget(self.snapshot_time)
        auto_layout.addLayout(time_layout)
        
        # 快照间隔
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("快照间隔 (小时):"))
        self.snapshot_interval = QSpinBox()
        self.snapshot_interval.setRange(1, 168)  # 1小时到1周
        self.snapshot_interval.setValue(self.config["auto_snapshot"]["interval"])
        interval_layout.addWidget(self.snapshot_interval)
        auto_layout.addLayout(interval_layout)
        
        auto_layout.addStretch()
        tabs.addTab(auto_tab, "自动快照")
        
        layout.addWidget(tabs)
        
        # 按钮
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def load_config(self) -> dict:
        """加载配置文件"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log.error("加载配置文件失败: %s", e)
        return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """保存配置"""
        try:
            config = {
                "compression": self.comp_algo.currentText(),
                "max_history": self.max_history.value(),
                "whitelist": [p.strip() for p in self.whitelist.toPlainText().split("\n") if p.strip()],
                "blacklist": [p.strip() for p in self.blacklist.toPlainText().split("\n") if p.strip()],
                "auto_snapshot": {
                    "enabled": self.auto_enabled.currentIndex() == 1,
                    "time": self.snapshot_time.currentText(),
                    "interval": self.snapshot_interval.value(),
                }
            }
            
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            self.config = config
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}") 