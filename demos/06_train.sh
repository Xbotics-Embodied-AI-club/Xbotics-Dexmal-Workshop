#!/usr/bin/env bash
# 从数据到开训一条龙，两个模型并行：DM0.5（LoRA，5000 步）与 DW0.5（全量，20000 步）。
#
# 用法：DM_GPUS=0,1 DW_GPUS=2,3,4 LEROBOT_PY=<装了 lerobot 的 python> bash demos/06_train.sh
#   DM_GPUS 给 4 张卡时再加 PER_DEVICE=6：配方固定等效 batch 48 = 卡数 × 每卡 × 累积步数，
#   凑不整就报错，不悄悄换配方。
#
# 里面依次是：数据验收 → 转成 dexdata → 画面与动作对齐校验 → DW0.5 文本嵌入 →
# 剔掉 DW05-Robotwin 里与双臂机器人绑定的权重 → DW0.5 归一化统计 → 并行开训。
# 每一步做什么、为什么，见 third_party/dexbotic/docs/so101.md。
# 训完用 04 号脚本验收：bash demos/04_dm05_eval_full.sh $SO101_ROOT/runs/dm05_so101/checkpoint-5000
set -euo pipefail
source "$(dirname "$0")/00_env.sh"
cd "$DEXBOTIC"
bash script/so101/run_pipeline.sh
echo "训练在后台跑，日志在 $SO101_RUNS_ROOT/logs/"
