"""把下载好的仿真与真机数据转成 DM0.5 / DW0.5 训练用的统一格式（dexdata）。

    python scripts/prepare_data.py

输入（`scripts/download.py --data` 下好的位置）：
    <数据目录>/so101-sim-640-v2/{cube40,cube20,cylinder40}   仿真三个场景
    <数据目录>/so101-real/<任务名>/                           真机九个任务
输出：训练配置 `DM05DataConfig` 读取的那个 dexdata 目录（jsonl 标注，画面仍引用原视频）

仿真与真机进同一份：同一台机器人、同样的六维动作、同样两路相机和帧率，本来就该共用一份
归一化统计；不同任务靠每一帧的指令区分。
"""

from __future__ import annotations

import pathlib
import sys


def main() -> int:
    from dexbotic.so101 import lerobot_v3_to_dexdata
    from dexbotic.so101.dm05_exp import DM05DataConfig

    # 输出写到训练读取的位置；dexdata 里视频的 url 相对 image_dir，转换时的 --image-root 必须同值。
    root = pathlib.Path(DM05DataConfig.image_dir)
    out = pathlib.Path(DM05DataConfig.jsonl_dir).parent
    sim, real = root / "so101-sim-640-v2", root / "so101-real"
    for directory in (sim, real):
        if not directory.is_dir():
            raise SystemExit(f"数据不在 {directory}；先运行 python scripts/download.py --data")

    # 每个场景 / 任务是一份 LeRobot 数据集，目录名就是它的名字。下载工具会在同级留下 .cache 之类的
    # 目录，所以按数据集自带的 meta/info.json 认，不按「是目录」认。
    def datasets(parent: pathlib.Path) -> list[pathlib.Path]:
        return sorted(d for d in parent.iterdir() if (d / "meta" / "info.json").is_file())

    sources = [(d, f"sim_{d.name}") for d in datasets(sim)] + [(d, f"real_{d.name}") for d in datasets(real)]
    argv = ["--out", str(out), "--image-root", str(root)]
    for directory, name in sources:
        argv += ["--source", str(directory), "--name", name]
    print(f"共 {len(sources)} 个来源 → {out}")
    sys.argv = ["lerobot_v3_to_dexdata", *argv]
    return lerobot_v3_to_dexdata.main()


if __name__ == "__main__":
    raise SystemExit(main())
