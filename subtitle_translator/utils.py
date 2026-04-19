"""
工具函数
"""
import os
from pathlib import Path


def chunk_list(lst, chunk_size: int):
    """将列表按指定大小分块"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def ensure_dir(path: str):
    """确保目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)


def get_output_path(input_path: str, suffix: str = "_zh") -> str:
    """生成输出文件路径，例如 input.srt -> input_zh.srt"""
    p = Path(input_path)
    return str(p.parent / f"{p.stem}{suffix}{p.suffix}")


def format_time(seconds: float) -> str:
    """将秒数格式化为 HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
