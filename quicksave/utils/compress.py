"""
提供 compress_dir / decompress_file，两种算法可选：
- 默认 `zstd`（需系统命令 `zstd`）
- 备选 `lz4`  （若 zstd 不存在自动降级）
"""
import os
import pathlib
import shutil
import subprocess
import tempfile
from typing import Literal
from .logger import log

ALG_ZSTD = shutil.which("zstd") is not None
ALG_LZ4  = shutil.which("lz4")  is not None

if not (ALG_ZSTD or ALG_LZ4):
    raise RuntimeError("Please install either `zstd` or `lz4` in PATH")


def _compress_cmd(out_path: pathlib.Path, level: int = 19) -> list[str]:
    if ALG_ZSTD:
        return ["zstd", f"-{level}", "--quiet", "-o", str(out_path)]
    else:
        return ["lz4", "-z", "-q", "-9", "-o", str(out_path)]


def _decompress_cmd(qsnap: pathlib.Path, out_path: pathlib.Path) -> list[str]:
    # 支持 .qsnap、.bak、.qsnap.bak
    fname = str(qsnap)
    if (fname.endswith(".qsnap") or fname.endswith(".qsnap.bak") or fname.endswith(".bak")) and ALG_ZSTD:
        return ["zstd", "-d", "--quiet", "-o", str(out_path), str(qsnap)]
    if (fname.endswith(".qsnap") or fname.endswith(".qsnap.bak") or fname.endswith(".bak")) and ALG_LZ4:
        return ["lz4", "-d", "-q", "-o", str(out_path), str(qsnap)]
    raise ValueError("Unsupported compression format")


def compress_dir(src_dir: pathlib.Path, dst_file: pathlib.Path) -> None:
    """
    把 src_dir 打包成 tar 并压缩为 dst_file (.qsnap)。
    """
    dst_tmp = dst_file.with_suffix(".tar")
    log.debug("tar -> %s", dst_tmp)
    subprocess.run(
        ["tar", "-C", src_dir, "-cf", str(dst_tmp), "."],
        check=True,
        stdin=subprocess.DEVNULL,
    )
    cmd = _compress_cmd(dst_file)
    log.debug("compress → %s", " ".join(cmd))
    with open(dst_tmp, "rb") as fin:
        subprocess.run(cmd, check=True, stdin=fin)
    os.remove(dst_tmp)


def decompress_file(qsnap: pathlib.Path, dst_dir: pathlib.Path) -> None:
    """
    解压 qsnap 到 dst_dir（产生 tar，再展开）。
    """
    tmp_tar = pathlib.Path(tempfile.mktemp(dir=dst_dir, suffix=".tar"))
    cmd = _decompress_cmd(qsnap, tmp_tar)
    subprocess.run(cmd, check=True, stdin=subprocess.DEVNULL)
    subprocess.run(
        ["tar", "-C", dst_dir, "-xf", str(tmp_tar)],
        check=True,
        stdin=subprocess.DEVNULL,
    )
    os.remove(tmp_tar)