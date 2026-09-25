#!/usr/bin/env bash
# DW0.5 推演未来：拿 02 号脚本在仿真里真实跑出的轨迹，给 DW0.5 第一帧画面和那串动作，
# 让它画出「照这串动作做下去会看到什么」，再和仿真真实发生的画面对比。
#
# 用法：GPU=0 bash demos/03_dw05_imagine.sh（先跑 02）
#
# 对比三行：仿真真值 / 按真实动作推演 / 按时间倒放的同一串动作推演。
# 真动作那行应当最像真值；倒放那行明显不同，说明模型在按动作推演，而不是放一段固定视频。
# 结论写在 dw05_sim_check.json：平均 PSNR 真动作要同时高于「复制第一帧」和「倒放」。
set -euo pipefail
source "$(dirname "$0")/00_env.sh"
GPU=${GPU:-0}
OUT=$OUTPUTS/03_imagine
cd "$DEXBOTIC"

CUDA_VISIBLE_DEVICES=$GPU "$PY" script/so101/dw05_sim_check.py \
  --checkpoint "$DW05_FINETUNED/model.pt" --norm-stats "$DW05_FINETUNED/norm_stats.json" \
  --bundle "$DW05_BUNDLE" --rollout-dir "$OUTPUTS/02_rollout" --out "$OUT" --per-scene 2
echo "对比视频与 dw05_sim_check.json 在 $OUT/"
