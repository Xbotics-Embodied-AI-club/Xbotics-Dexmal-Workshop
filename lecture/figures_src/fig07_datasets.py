"""图 7、图 8：训练数据长什么样。

图 7 是 12 个数据来源各一帧顶视画面（仿真 3 个场景 + 真机 9 个任务）；图 8 是一集仿真数据：
上面几帧画面，下面是同一集逐帧的关节状态，竖线标出画面所在的时刻。

两张图都从转换好的 Dexdata 读：每集一个 jsonl，每行一帧，记着状态和画面在原视频里的位置。
数据目录与训练读的是同一处（`dexbotic.so101.dm05_exp.DM05DataConfig`，设 `SO101_DATASETS_DIR`
可以指到别处），先运行过 `scripts/download.py --data` 与 `scripts/prepare_data.py` 才有。
"""

import json
import subprocess
from pathlib import Path

import figstyle
import matplotlib.pyplot as plt
import numpy as np
from dexbotic.so101.dm05_exp import DM05DataConfig

#: jsonl 里视频的 url 相对 image_dir。
ROOT = Path(DM05DataConfig.image_dir)
JSONL = Path(DM05DataConfig.jsonl_dir)
#: 图 7 的格子：jsonl 文件名前缀 → 图上的名字。
TASKS = {
    "sim_cube40": "仿真 · 4 cm 方块",
    "sim_cube20": "仿真 · 2 cm 方块",
    "sim_cylinder40": "仿真 · 罐子",
    "real_pick_up_a_cube_and_place_in_the_bin": "真机 · 方块",
    "real_pick_up_a_can_and_place_in_the_bin": "真机 · 罐子",
    "real_pick_up_a_battery_and_place_in_the_bin": "真机 · 电池",
    "real_pick_up_a_eraser_and_place_in_the_bin": "真机 · 橡皮",
    "real_pick_up_a_golf_and_place_in_the_bin": "真机 · 高尔夫球",
    "real_pick_up_a_medicine_bottle_and_place_in_the_bin": "真机 · 药瓶",
    "real_pick_up_a_plush_toy_and_place_in_the_bin": "真机 · 毛绒玩具",
    "real_Stack_the_cube_on_the_can": "真机 · 方块叠到罐子上",
    "real_Stack_the_smaller_cube_on_the_larger_one": "真机 · 小方块叠到大方块上",
}
#: 图 7 取这一集里多靠后的一帧（0 为第一帧，1 为最后一帧）：机械臂刚起步、物体还没被挡住。
#: 第 k 格取第 k 集 —— 仿真三个场景的第 0 集用的是同一个摆放种子，全取第 0 集三格会一模一样。
POSITION = 0.1
#: 图 8 用的那一集，与讲义第 6.2 节摆出的 jsonl 第一行是同一集。
EPISODE_FILE = "sim_cube40_ep00000.jsonl"
KEYFRAMES = 5
JOINTS = ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll")
LABELS = ("时间（秒）", "关节角（度）", "夹爪开合", "第", "帧", "顶视", "腕部")


def load(name: str) -> list[dict]:
    with open(JSONL / name) as f:
        return [json.loads(line) for line in f]


def frame(ref: dict) -> np.ndarray:
    """按 jsonl 里的视频地址与帧号取一帧（30 帧/秒，按时间定位）。"""
    raw = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-ss",
            f"{ref['frame_idx'] / 30:.4f}",
            "-i",
            str(ROOT / ref["url"]),
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-",
        ],
        check=True,
        capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(480, 640, 3)


def task_grid(font: str) -> None:
    fig, axes = plt.subplots(3, 4, figsize=(10, 5.9))
    for k, (ax, (prefix, title)) in enumerate(zip(axes.flat, TASKS.items(), strict=True)):
        rows = load(f"{prefix}_ep{k:05d}.jsonl")
        ax.imshow(frame(rows[int(POSITION * (len(rows) - 1))]["images_1"]))
        ax.set_title(title, fontsize=9.5)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.subplots_adjust(wspace=0.04, hspace=0.18)
    figstyle.save(fig, "fig-07-datasets.png", font)


def episode(font: str) -> None:
    rows = load(EPISODE_FILE)
    state = np.array([r["state"] for r in rows])
    t = np.arange(len(rows)) / 30
    picks = np.linspace(0, len(rows) - 1, KEYFRAMES).astype(int)
    fig = plt.figure(figsize=(10, 6.6))
    grid = fig.add_gridspec(4, KEYFRAMES, height_ratios=[1, 1, 1.25, 0.8], hspace=0.12, wspace=0.04)
    for col, i in enumerate(picks):
        for row, key in enumerate(("images_1", "images_2")):
            ax = fig.add_subplot(grid[row, col])
            ax.imshow(frame(rows[i][key]))
            ax.set_xticks([])
            ax.set_yticks([])
            if row == 0:
                ax.set_title(f"第 {i} 帧（{t[i]:.1f} 秒）", fontsize=9.5)
            if col == 0:
                ax.set_ylabel(LABELS[5 + row], fontsize=10)
    joints = fig.add_subplot(grid[2, :])
    for k, name in enumerate(JOINTS):
        joints.plot(t, state[:, k], lw=1.3, label=name)
    joints.set_ylabel(LABELS[1])
    joints.legend(fontsize=8, loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False)
    joints.tick_params(labelbottom=False)
    gripper = fig.add_subplot(grid[3, :], sharex=joints)
    gripper.plot(t, state[:, 5], color="#444444", lw=1.3)
    gripper.set_ylabel(LABELS[2])
    gripper.set_xlabel(LABELS[0])
    for ax in (joints, gripper):
        ax.grid(alpha=0.3)
        for i in picks:
            ax.axvline(t[i], color="#999999", lw=0.8, ls="--")
    fig.align_ylabels([joints, gripper])
    figstyle.save(fig, "fig-08-episode.png", font)


def main() -> None:
    font = figstyle.apply()
    figstyle.assert_covered("".join(TASKS.values()) + "".join(LABELS) + "（）", "图 7、图 8")
    task_grid(font)
    episode(font)


if __name__ == "__main__":
    main()
