"""图 5：DW0.5 推演未来，三行对照 —— 仿真真值 / 按真实动作推演 / 按倒放动作推演。

源是 media/dw05_imagine_cube40.mp4：三行上下拼接，每行 384 像素高，左上角压着一条英文标签。
标签不是讲义字体，所以每行裁掉顶上 26 像素（那一带是空旷背景），行名在这里重写。
每帧是模型输入的拼法：上方大图为顶视，下方两小图为腕部（同一路腕部画面复用了一次）。
"""

import figstyle
import matplotlib.pyplot as plt
import numpy as np
from frames import MEDIA, read_frames, save

ROW_H = 384
LABEL_H = 26
TIMES = 5
ROWS = ("仿真真值", "按真实动作推演", "按倒放动作推演")


def main() -> None:
    font = figstyle.apply()
    figstyle.assert_covered("".join(ROWS) + "第帧", "图 5")
    frames = read_frames(MEDIA / "dw05_imagine_cube40.mp4")
    # 裁图按固定的行高与标签高算；视频重出后尺寸一变，裁出来会悄悄错位，所以先核对。
    assert frames.shape[1] == 3 * ROW_H, frames.shape
    picks = np.linspace(0, len(frames) - 1, TIMES).astype(int)
    fig, axes = plt.subplots(3, TIMES, figsize=(1.9 * TIMES, 6.4))
    for col, t in enumerate(picks):
        for row in range(3):
            ax = axes[row, col]
            ax.imshow(frames[t, row * ROW_H + LABEL_H : (row + 1) * ROW_H])
            ax.set_xticks([])
            ax.set_yticks([])
            if row == 0:
                ax.set_title(f"第 {t} 帧", fontsize=10)
            if col == 0:
                ax.set_ylabel(ROWS[row], fontsize=10)
    fig.subplots_adjust(wspace=0.03, hspace=0.04)
    save(fig, "fig-05-dw05-compare.png", font)


if __name__ == "__main__":
    main()
