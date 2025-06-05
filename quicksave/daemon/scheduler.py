"""
快照调度器，用于定时创建快照。
"""
import json
import pathlib
import time
from datetime import datetime, timedelta
from threading import Thread

from ..utils.logger import log
from ..core import dump

class SnapshotScheduler(Thread):
    def __init__(self, config_path: pathlib.Path):
        super().__init__(daemon=True)
        self.config_path = config_path
        self.running = True
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
            "auto_snapshot": {
                "enabled": False,
                "time": "22:00",
                "interval": 24,  # 小时
            }
        }
    
    def get_next_snapshot_time(self) -> datetime:
        """计算下次快照时间"""
        now = datetime.now()
        target_time = datetime.strptime(self.config["auto_snapshot"]["time"], "%H:%M").time()
        target = datetime.combine(now.date(), target_time)
        
        if now > target:
            target += timedelta(days=1)
        
        return target
    
    def run(self):
        """调度快照任务"""
        while self.running:
            try:
                if self.config["auto_snapshot"]["enabled"]:
                    next_time = self.get_next_snapshot_time()
                    wait_seconds = (next_time - datetime.now()).total_seconds()
                    
                    if wait_seconds > 0:
                        time.sleep(wait_seconds)
                    
                    if self.running:  # 再次检查，避免在睡眠时退出
                        log.info("执行定时快照")
                        # TODO: 实现进程选择逻辑
                        pids = [1234]  # 示例 PID
                        dump(pids, label="scheduled")
                
                # 等待下一个检查点
                time.sleep(60)
                
            except Exception as e:
                log.error("调度快照失败: %s", e)
                time.sleep(60)
    
    def stop(self):
        """停止调度器"""
        self.running = False 