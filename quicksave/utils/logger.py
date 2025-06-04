import logging
import logging.handlers
import pathlib
import sys
from datetime import datetime

LOG_DIR = pathlib.Path.home() / ".quicksave" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

log = logging.getLogger("quicksave")
log.setLevel(logging.INFO)

# 控制台输出（仅 INFO+）
_stream = logging.StreamHandler(sys.stdout)
_stream.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
log.addHandler(_stream)

# 滚动文件：按日期新建
_today = datetime.now().strftime("%Y-%m-%d")
_file = LOG_DIR / f"{_today}.log"
_fh = logging.FileHandler(_file, encoding="utf-8")
_fh.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(module)s:%(lineno)d | %(message)s"
))
log.addHandler(_fh)