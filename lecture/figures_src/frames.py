"""从本仓 media/ 的视频里取帧，供出图脚本拼图用。

走 ffmpeg 解码成原始 RGB 字节再读成数组，出图环境不必另装 Python 的视频解码库；
需要系统里有 ffmpeg 与 ffprobe。
"""

import json
import subprocess
from pathlib import Path

import numpy as np

LECTURE = Path(__file__).resolve().parents[1]
MEDIA = LECTURE.parent / "media"
FIGURES = LECTURE / "figures"
DATA = LECTURE / "data"


def read_frames(path: Path) -> np.ndarray:
    """整段视频解成 (T, H, W, 3) 的 uint8 数组。"""
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    stream = json.loads(probe.stdout)["streams"][0]
    width, height = stream["width"], stream["height"]
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        check=True,
        capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, height, width, 3)


def save(fig, name: str, font: str) -> Path:
    """按讲义引用的文件名存图，并把字体名写进元数据，用图本身证明用的是哪套字体。"""
    FIGURES.mkdir(exist_ok=True)
    out = FIGURES / name
    fig.savefig(out, dpi=200, bbox_inches="tight", metadata={"Font": font})
    return out
