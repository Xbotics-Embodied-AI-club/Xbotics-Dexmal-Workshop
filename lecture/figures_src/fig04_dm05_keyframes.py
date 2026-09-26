"""图 4：DM0.5 在仿真里抓放 2 cm 方块的一局，上行顶视、下行腕部，六个时刻。

源是 media/dm05_cube20_success.mp4：左右并排的顶视与腕部画面，顶上 44 像素是标注横幅。
横幅用的不是讲义字体，所以裁掉，时刻标注在这里重写。
"""

import figstyle
import matplotlib.pyplot as plt
import numpy as np
from dexbotic.so101.client import read_frames

BANNER = 44
VIEW_H, VIEW_W = 480, 640
TIMES = 6


def main() -> None:
    font = figstyle.apply()
    frames = read_frames(figstyle.MEDIA / "dm05_cube20_success.mp4")
    # 裁图按固定的横幅高与画面尺寸算；视频重出后尺寸一变，裁出来会悄悄错位，所以先核对。
    # 编码时高度补齐到 16 的倍数，底下多出几行空白，所以高度只要求放得下。
    assert frames.shape[2] == 2 * VIEW_W and frames.shape[1] >= BANNER + VIEW_H, frames.shape
    picks = np.linspace(0, len(frames) - 1, TIMES).astype(int)
    rows = ("顶视相机", "腕部相机")
    figstyle.assert_covered("".join(rows) + "第步", "图 4")
    # 每格 1.4 英寸宽：按版心宽缩放后，11 pt 的标注印出来约 8 pt。
    fig, axes = plt.subplots(2, TIMES, figsize=(1.4 * TIMES, 2.4))
    for col, t in enumerate(picks):
        body = frames[t, BANNER : BANNER + VIEW_H]
        for row, view in enumerate((body[:, :VIEW_W], body[:, VIEW_W : 2 * VIEW_W])):
            ax = axes[row, col]
            ax.imshow(view)
            ax.set_xticks([])
            ax.set_yticks([])
            if row == 0:
                ax.set_title(f"第 {t} 步", fontsize=11)
            if col == 0:
                ax.set_ylabel(rows[row], fontsize=11)
    fig.subplots_adjust(wspace=0.03, hspace=0.05)
    figstyle.save(fig, "fig-04-dm05-keyframes.png", font)


if __name__ == "__main__":
    main()
