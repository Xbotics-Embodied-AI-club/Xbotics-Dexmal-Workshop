"""图 6：单卡 LoRA 现场配方（每次参数更新 48 个样本、300 步）的训练损失。

数据在 lecture/data/lora_single_gpu.json：训练日志里逐步记录的损失（取自训练器保存的日志历史）。
单步损失是在当步那一批样本上算的，抖动很大，这里画滑动平均看趋势。
"""

import json

import figstyle
import matplotlib.pyplot as plt
import numpy as np

LABELS = ("训练步数", "训练损失")


def smooth(y: np.ndarray, k: int = 9) -> np.ndarray:
    pad = np.pad(y, (k // 2, k // 2), mode="edge")
    return np.convolve(pad, np.ones(k) / k, mode="valid")


def main() -> None:
    font = figstyle.apply()
    figstyle.assert_covered("".join(LABELS), "图 6")
    data = json.loads((figstyle.DATA / "lora_single_gpu.json").read_text())
    steps, loss = np.array(data["log"]).T
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    ax.plot(steps, loss, color="#bbbbbb", lw=0.8)
    ax.plot(steps, smooth(loss), color="#1f77b4", lw=1.6)
    ax.set_xlabel(LABELS[0])
    ax.set_ylabel(LABELS[1])
    ax.grid(alpha=0.3)
    figstyle.save(fig, "fig-06-lora-loss.png", font)


if __name__ == "__main__":
    main()
