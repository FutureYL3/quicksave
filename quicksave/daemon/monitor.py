"""
进程监控器，用于监控进程活跃度。
"""
import json
import pathlib
import psutil
import time
from threading import Thread
from typing import List, Set

from ..utils.logger import log
from ..core import dump

class ProcessMonitor(Thread):
    def __init__(self, config_path: pathlib.Path):
        super().__init__(daemon=True)
        self.config_path = config_path
        self.running = True
        self.last_snapshot = 0
        self.config = self.load_config()
    
    def load_config(self) -> dict:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log.error("加载配置文件失败: %s", e)
        return {
            "whitelist": [],
            "blacklist": [],
            "min_interval": 3600,  # 最小快照间隔（秒）
        }
    
    def get_target_pids(self) -> List[int]:
        """获取需要监控的进程 PID 列表"""
        target_pids = set()
        
        # 获取所有进程
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info['name'].lower()
                # 检查白名单
                if self.config["whitelist"]:
                    if name in self.config["whitelist"]:
                        target_pids.add(proc.info['pid'])
                # 检查黑名单
                elif name not in self.config["blacklist"]:
                    target_pids.add(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return list(target_pids)
    
    def should_take_snapshot(self) -> bool:
        """判断是否应该创建快照"""
        now = time.time()
        if now - self.last_snapshot < self.config["min_interval"]:
            return False
        
        pids = self.get_target_pids()
        if not pids:
            return False
        
        return True
    
    def run(self):
        """监控进程并创建快照"""
        while self.running:
            try:
                if self.should_take_snapshot():
                    pids = self.get_target_pids()
                    if pids:
                        log.info("创建自动快照: %s", pids)
                        dump(pids, label="auto")
                        self.last_snapshot = time.time()
            except Exception as e:
                log.error("监控进程失败: %s", e)
            
            time.sleep(60)  # 每分钟检查一次
    
    def stop(self):
        """停止监控"""
        self.running = False 