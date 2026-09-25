"""图 1：一天的路线。上午一行是主线（实线框），下午一行是拓展（虚线框）。"""

import figstyle
import matplotlib.pyplot as plt
from frames import save
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

MORNING = [
    ("认识框架", "第 2 节"),
    ("认识机械臂", "第 3 节"),
    ("DM0.5 仿真抓放", "第 4 节"),
    ("DW0.5 推演未来", "第 5 节"),
]
AFTERNOON = [("认识数据集", "第 6 节"), ("单卡微调 DM0.5", "第 7 节"), ("真机部署", "第 8 节")]
ROW_LABELS = ("上午：主线", "下午：拓展")
W, H, GAP = 0.18, 0.3, 0.035


def row(ax, items, y, dashed: bool) -> None:
    x = 0.14
    for i, (title, where) in enumerate(items):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                W,
                H,
                boxstyle="round,pad=0.01",
                lw=1.1,
                fc="#f8f1e7" if dashed else "#eef3f8",
                ec="#333333",
                ls=(0, (4, 3)) if dashed else "-",
            )
        )
        ax.text(x + W / 2, y + H * 0.62, title, ha="center", va="center", fontsize=10.5)
        ax.text(x + W / 2, y + H * 0.28, where, ha="center", va="center", fontsize=9, color="#555555")
        if i < len(items) - 1:
            ax.add_patch(
                FancyArrowPatch(
                    (x + W, y + H / 2),
                    (x + W + GAP, y + H / 2),
                    arrowstyle="-|>",
                    mutation_scale=12,
                    lw=1.1,
                    color="#333333",
                )
            )
        x += W + GAP


def main() -> None:
    font = figstyle.apply()
    text = "".join(t + w for t, w in MORNING + AFTERNOON) + "".join(ROW_LABELS)
    figstyle.assert_covered(text, "图 1")
    fig, ax = plt.subplots(figsize=(7.2, 2.0))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set_xlim(0, 1.0)
    ax.set_ylim(0, 1)
    ax.axis("off")
    for label, y in zip(ROW_LABELS, (0.6, 0.1), strict=True):
        ax.text(0.01, y + H / 2, label, ha="left", va="center", fontsize=10.5)
    row(ax, MORNING, 0.6, dashed=False)
    row(ax, AFTERNOON, 0.1, dashed=True)
    save(fig, "fig-01-roadmap.png", font)


if __name__ == "__main__":
    main()
