"""DW0.5 推演未来：拿 rollout 在仿真里真实跑出的轨迹，按真实动作推演画面，再与两个参照比。

    python -m dexmal_workshop.imagine --rollout-dir <rollout 的输出目录>

对照三行：仿真真值 / 按真实动作推演 / 按时间倒放的同一串动作推演。判据写在
`<输出目录>/dw05_sim_check.json` 的 `passed`：真实动作的平均 PSNR 同时高于「复制起始帧」
和「倒放动作」，且逐条胜过倒放的占多数。
"""

from __future__ import annotations

import argparse
import pathlib
import sys


def main() -> int:
    from dexbotic.so101 import dw05_sim_check
    from dexbotic.so101.layout import DW05_BUNDLE, ROOT, WEIGHTS_DIR

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rollout-dir", required=True, type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path(ROOT) / "outputs" / "imagine")
    ap.add_argument("--per-scene", type=int, default=2, help="每个场景取几条轨迹")
    args = ap.parse_args()
    weights = pathlib.Path(WEIGHTS_DIR) / "so101-dw05"
    sys.argv = [
        "imagine",
        "--checkpoint",
        str(weights / "model.pt"),
        "--norm-stats",
        str(weights / "norm_stats.json"),
        "--bundle",
        DW05_BUNDLE,
        "--rollout-dir",
        str(args.rollout_dir),
        "--out",
        str(args.out),
        "--per-scene",
        str(args.per_scene),
    ]
    return dw05_sim_check.main()


if __name__ == "__main__":
    raise SystemExit(main())
