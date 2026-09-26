"""把 rollout 存下的单局录像做成 top | wrist 并排的片子，顶上横幅写明来历。

横幅写清哪个模型、哪个场景、第几局、成没成、是策略在仿真里还是真机上跑的 ——
没有这行字，策略 rollout 与数据集里同样两路并排的演示录像肉眼分不开。

用法：
    python scripts/label_videos.py --rollout-dir <rollout 的输出目录> --out <目录> [--per-kind 2]

每个场景的成功、失败各取前 `--per-kind` 局。
"""

import argparse
import pathlib

import av
import imageio.v3 as iio
import numpy as np
from dexbotic.so101.client import parse_episode_stem, read_frames
from PIL import Image, ImageDraw, ImageFont


def banner(width: int, text: str, ok: bool) -> np.ndarray:
    img = Image.new("RGB", (width, 44), (20, 110, 40) if ok else (150, 30, 30))
    ImageDraw.Draw(img).text((12, 8), text, fill=(255, 255, 255), font=ImageFont.load_default(size=24))
    return np.asarray(img)


def video_fps(path: pathlib.Path) -> float:
    with av.open(str(path)) as container:
        return float(container.streams.video[0].average_rate)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rollout-dir", required=True, type=pathlib.Path)
    ap.add_argument("--out", required=True, type=pathlib.Path)
    ap.add_argument("--per-kind", type=int, default=2, help="每个场景成功、失败各出几段")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    picked: dict[tuple[str, str], list[pathlib.Path]] = {}
    for top_path in sorted((args.rollout_dir / "videos").glob("*.mp4")):
        if top_path.stem.endswith("_wrist"):
            continue
        _, scene, _, kind = parse_episode_stem(top_path.stem)
        group = picked.setdefault((scene, kind), [])
        if len(group) < args.per_kind:
            group.append(top_path)
    made = []
    for top_path in (p for group in picked.values() for p in group):
        label, scene, episode, kind = parse_episode_stem(top_path.stem)
        top = read_frames(top_path)
        wrist = read_frames(top_path.with_name(top_path.stem + "_wrist.mp4"))
        n = min(len(top), len(wrist))
        fps = video_fps(top_path)
        where = "on the real SO-101" if scene == "real" else "in so101_sim"
        text = (
            f"{label} policy rollout {where} | {scene} {episode} | "
            f"{'SUCCESS' if kind == 'success' else 'FAIL'} | {n} steps @{fps:g}fps | left: top  right: wrist"
        )
        head = banner(top.shape[2] + wrist.shape[2], text, kind == "success")
        frames = [np.concatenate([head, np.concatenate([top[t], wrist[t]], axis=1)], axis=0) for t in range(n)]
        dst = args.out / f"{top_path.stem}.mp4"
        iio.imwrite(str(dst), np.stack(frames), fps=fps, codec="libx264")
        made.append(dst.name)
    print("\n".join(made) or "没有可用的录像")
    return 0 if made else 1


if __name__ == "__main__":
    raise SystemExit(main())
