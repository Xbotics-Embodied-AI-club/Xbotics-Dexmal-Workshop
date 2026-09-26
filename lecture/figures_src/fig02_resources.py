"""图 2：教学仓安装时自动取来的依赖，以及权重和数据从哪里来。

教学仓直接依赖 Dexbotic 与 LeRobot；仿真器是 LeRobot 的依赖，注册成 LeRobot 的一种机器人，随 LeRobot 一起装上。
"""

import figstyle
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

H = 0.15
#: 名字 → (左下 x, 左下 y, 宽, 文字, 底色)
BOXES = {
    "repo": (0.36, 0.44, 0.28, "教学仓\n讲义与工作坊脚本", "#f8f1e7"),
    "dexbotic": (0.02, 0.80, 0.28, "Dexbotic\nDM0.5 与 DW0.5 的框架", "#eef3f8"),
    "lerobot": (0.36, 0.80, 0.28, "LeRobot\n仿真与真机的统一接口", "#eef3f8"),
    "sim": (0.70, 0.80, 0.28, "SO-101 仿真器\n注册为 LeRobot 的一种机器人", "#eef3f8"),
    "weights": (0.10, 0.06, 0.34, "权重（Hugging Face）\nDM0.5、DW0.5 微调权重", "#eaf5ea"),
    "data": (0.56, 0.06, 0.34, "数据（Hugging Face、ModelScope）\n仿真 1498 集、真机 2200 集", "#eaf5ea"),
}
LABELS = ("uv sync 自动安装", "download --weights", "download --data", "依赖")


def box(ax, key) -> tuple[float, float, float]:
    x, y, w, text, face = BOXES[key]
    ax.add_patch(FancyBboxPatch((x, y), w, H, boxstyle="round,pad=0.01", fc=face, ec="#333333", lw=1.0))
    ax.text(x + w / 2, y + H / 2, text, ha="center", va="center", fontsize=9.5, linespacing=1.35)
    return x, y, w


def arrow(ax, start, end) -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12, lw=1.1, color="#333333"))


def main() -> None:
    font = figstyle.apply()
    figstyle.assert_covered("".join(b[3] for b in BOXES.values()) + "".join(LABELS), "图 2")
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set_xlim(-0.01, 1.01)
    ax.set_ylim(-0.01, 1.0)
    ax.axis("off")
    for key in BOXES:
        box(ax, key)
    top = 0.44 + H
    for key in ("dexbotic", "lerobot"):
        x, y, w = BOXES[key][:3]
        arrow(ax, (0.5, top), (x + w / 2, y))
    # 仿真器不由教学仓直接依赖，而是 LeRobot 的依赖。
    arrow(ax, (0.64, 0.80 + H / 2), (0.70, 0.80 + H / 2))
    ax.text(0.67, 0.80 + H / 2 + 0.035, LABELS[3], ha="center", va="bottom", fontsize=9, color="#555555")
    ax.text(
        0.36,
        0.70,
        LABELS[0],
        ha="center",
        va="center",
        fontsize=9,
        color="#555555",
        bbox={"fc": "white", "ec": "none", "pad": 1},
    )
    for key, label in (("weights", LABELS[1]), ("data", LABELS[2])):
        x, y, w = BOXES[key][:3]
        arrow(ax, (0.5, 0.44), (x + w / 2, y + H))
        ax.text(
            (0.5 + x + w / 2) / 2,
            0.30,
            label,
            ha="center",
            va="center",
            fontsize=9,
            color="#555555",
            bbox={"fc": "white", "ec": "none", "pad": 1},
        )
    figstyle.save(fig, "fig-02-resources.png", font)


if __name__ == "__main__":
    main()
