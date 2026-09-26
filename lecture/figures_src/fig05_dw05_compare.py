"""图 5：DW0.5 推演未来，三行对照 —— 仿真真值 / 按真实动作推演 / 按倒放动作推演。

源是 media/dw05_imagine_cube40.mp4：三行上下拼接，每行 384 像素高，左上角压着一条英文标签。
标签不是讲义字体，所以每行裁掉顶上 26 像素（那一带是空旷背景），行名在这里重写。
每行是模型输入的拼法：上方大图为顶视，一条黑色分隔带下面并排两张腕部图。SO-101 只有一路
腕部相机，为了凑成模型预训练时的三路布局，同一路腕部画面放了两次，所以两张完全相同；
图里只取左边那一张，顶视与腕部分成上下两行画。
"""

import figstyle
import matplotlib.pyplot as plt
import numpy as np
from frames import MEDIA, read_frames, save

ROW_H = 384
LABEL_H = 26
TIMES = 5
ROWS = ("仿真真值", "按真实动作推演", "按倒放动作推演")
VIEWS = ("顶视", "腕部")


def split(band: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """一行拆成顶视与（左边那张）腕部：按中间那条近乎全黑的分隔带切开。"""
    dark = np.flatnonzero(band.mean(axis=(1, 2)) < 40)
    # 分隔带在行的中段；底边若有黑框也会被选进来，所以只认中段第一段连续的暗行。
    dark = dark[(dark > band.shape[0] // 3) & (dark < band.shape[0] * 5 // 6)]
    assert len(dark) and np.all(np.diff(dark) == 1), dark
    return band[: dark[0]], band[dark[-1] + 1 :, : band.shape[1] // 2]


def main() -> None:
    font = figstyle.apply()
    figstyle.assert_covered("".join(ROWS + VIEWS) + "第帧", "图 5")
    frames = read_frames(MEDIA / "dw05_imagine_cube40.mp4")
    # 裁图按固定的行高与标签高算；视频重出后尺寸一变，裁出来会悄悄错位，所以先核对。
    assert frames.shape[1] == 3 * ROW_H, frames.shape
    picks = np.linspace(0, len(frames) - 1, TIMES).astype(int)
    top, wrist = split(frames[0, LABEL_H:ROW_H])
    ratios = [top.shape[0] / top.shape[1], wrist.shape[0] / wrist.shape[1]] * 3
    fig, axes = plt.subplots(6, TIMES, figsize=(1.9 * TIMES, 1.9 * sum(ratios) + 0.5), height_ratios=ratios)
    for col, t in enumerate(picks):
        for row in range(3):
            views = split(frames[t, row * ROW_H + LABEL_H : (row + 1) * ROW_H])
            for k, image in enumerate(views):
                ax = axes[2 * row + k, col]
                ax.imshow(image)
                ax.set_xticks([])
                ax.set_yticks([])
                if col == 0:
                    ax.set_ylabel(f"{ROWS[row]}\n{VIEWS[k]}" if k == 0 else VIEWS[k], fontsize=9.5)
        axes[0, col].set_title(f"第 {t} 帧", fontsize=10)
    fig.subplots_adjust(wspace=0.03, hspace=0.05)
    # 三组之间多留一点空，看得出哪两行是一组。
    for row in (2, 4):
        for ax in axes[row:].flat:
            box = ax.get_position()
            ax.set_position([box.x0, box.y0 - 0.012, box.width, box.height])
    save(fig, "fig-05-dw05-compare.png", font)


if __name__ == "__main__":
    main()
