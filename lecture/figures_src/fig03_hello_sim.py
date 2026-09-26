"""图 3：仿真里的 SO-101 转动手腕、开合夹爪。源是 media/hello_robot.mp4（左顶视、右腕部并排）。"""

import figstyle
import matplotlib.pyplot as plt
import numpy as np
from dexbotic.so101.client import read_frames

VIEW_W = 640
TIMES = (0, 22, 45, 67)
ROWS = ("顶视相机", "腕部相机")


def main() -> None:
    font = figstyle.apply()
    figstyle.assert_covered("".join(ROWS) + "第步", "图 3")
    frames = read_frames(figstyle.MEDIA / "hello_robot.mp4")
    # 两路 640 宽的画面左右并排；视频重出后尺寸一变，裁出来会悄悄错位，所以先核对。
    assert frames.shape[2] == 2 * VIEW_W, frames.shape
    fig, axes = plt.subplots(2, len(TIMES), figsize=(1.8 * len(TIMES), 2.9))
    for col, t in enumerate(TIMES):
        for row, view in enumerate((frames[t, :, :VIEW_W], frames[t, :, VIEW_W:])):
            ax = axes[row, col]
            ax.imshow(np.asarray(view))
            ax.set_xticks([])
            ax.set_yticks([])
            if row == 0:
                ax.set_title(f"第 {t} 步", fontsize=11)
            if col == 0:
                ax.set_ylabel(ROWS[row], fontsize=11)
    fig.subplots_adjust(wspace=0.03, hspace=0.05)
    figstyle.save(fig, "fig-03-hello-sim.png", font)


if __name__ == "__main__":
    main()
