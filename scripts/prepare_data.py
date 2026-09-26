"""把下载好的仿真与真机数据转成 DM0.5 / DW0.5 训练用的统一格式（dexdata）。

    python scripts/prepare_data.py

输入（`scripts/download.py --data` 下好的位置）：
    <数据目录>/so101-sim-640-v2/{cube40,cube20,cylinder40}   仿真三个场景
    <数据目录>/so101-real/<任务名>/                           真机九个任务
输出：`dexbotic.so101.layout.DEXDATA_DIR`（两个模型的训练都从这里读；jsonl 标注，画面仍引用原视频）

仿真与真机进同一份：同一台机器人、同样的六维动作、同样两路相机和帧率，本来就该共用一份
归一化统计；不同任务靠每一帧的指令区分。
"""

from __future__ import annotations

import pathlib

from download import REAL_DATA_DIR, SIM_DATA_DIR


def main() -> int:
    from dexbotic.so101 import lerobot_v3_to_dexdata
    from dexbotic.so101.layout import DATASETS_DIR, DEXDATA_DIR

    # dexdata 里视频的 url 相对数据目录（训练配置的 image_dir 也是它），转换时的 --image-root 必须同值。
    root = pathlib.Path(DATASETS_DIR)
    sim, real = root / SIM_DATA_DIR, root / REAL_DATA_DIR
    for directory in (sim, real):
        if not directory.is_dir():
            raise SystemExit(f"数据不在 {directory}；先运行 python scripts/download.py --data")

    # 每个场景 / 任务是一份 LeRobot 数据集，目录名就是它的名字。下载工具会在同级留下 .cache 之类的
    # 目录，所以按数据集自带的 meta/info.json 认，不按「是目录」认。
    def datasets(parent: pathlib.Path) -> list[pathlib.Path]:
        return sorted(d for d in parent.iterdir() if (d / "meta" / "info.json").is_file())

    sources = [(d, f"sim_{d.name}") for d in datasets(sim)] + [(d, f"real_{d.name}") for d in datasets(real)]
    argv = ["--out", DEXDATA_DIR, "--image-root", str(root)]
    for directory, name in sources:
        argv += ["--source", str(directory), "--name", name]
    print(f"共 {len(sources)} 个来源 → {DEXDATA_DIR}")
    return lerobot_v3_to_dexdata.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
