import datetime
import os
import pathlib
import shutil
import subprocess
import tempfile
from typing import List

from quicksave.utils.logger import log
from quicksave.utils.timer import timed
from quicksave.utils.compress import compress_dir
from ._criu import build as criu_cmd

QS_DIR = pathlib.Path.home() / ".quicksave"
QS_DIR.mkdir(exist_ok=True)


@timed
def dump(pids: List[int], label: str | None = None) -> pathlib.Path:
    if not pids:
        raise ValueError("pids list cannot be empty")

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"{label}_" if label else ""
    out_file = QS_DIR / f"{prefix}{ts}.qsnap"

    tmp_dump = pathlib.Path(tempfile.mkdtemp(prefix="qs_dmp_"))
    leader = str(pids[0])
    root   = os.geteuid() == 0

    # ---------- root 分支 ----------
    if root:
        log.info("pre-dump pid=%s -> %s", leader, tmp_dump)
        subprocess.run(
            criu_cmd("pre-dump", "-t", leader, "-D", tmp_dump,
                     "--track-mem", "--shell-job"),
            check=True, stdin=subprocess.DEVNULL,
        )

        log.info("final dump (root)…")
        subprocess.run(
            criu_cmd("dump", "-t", leader, "-D", tmp_dump,
                     "--shell-job", "--tcp-established", "--ext-unix-sk", "--pty"),
            check=True, stdin=subprocess.DEVNULL,
        )

    # ---------- rootless 分支 ----------
    else:
        log.info("rootless dump pid=%s -> %s", leader, tmp_dump)
        subprocess.run(
            criu_cmd("dump", "-t", leader, "-D", tmp_dump,
                     "--shell-job", "--ext-unix-sk", "--pty"),
            check=True, stdin=subprocess.DEVNULL,
        )

    log.info("compress to %s", out_file)
    compress_dir(tmp_dump, out_file)
    shutil.rmtree(tmp_dump, ignore_errors=True)
    log.info("dump finished => %s (%.1f MiB)", out_file,
             out_file.stat().st_size / 2**20)
    return out_file