#!/usr/bin/env bash
# DM0.5 在仿真里抓放：起推理服务 → 仿真里跑几局 → 出带标注的录像。
#
# 用法：GPU=0 SCENE=cube40 EPISODES=5 bash demos/02_dm05_sim_rollout.sh
#   SCENE 取 cube40（4 cm 方块）/ cube20（2 cm 方块）/ cylinder40（罐子）
#
# 产物在 $SO101_ROOT/outputs/02_rollout/：videos/ 是逐局的顶视、腕部录像与逐步状态
# （04 号脚本拿它们喂 DW0.5），labeled/ 是 top | wrist 并排、顶上写明成败的片子。
set -euo pipefail
source "$(dirname "$0")/00_env.sh"
GPU=${GPU:-0}
SCENE=${SCENE:-cube40}
EPISODES=${EPISODES:-5}
PORT=7891
OUT=$OUTPUTS/02_rollout
mkdir -p "$OUT"
cd "$DEXBOTIC"

CUDA_VISIBLE_DEVICES=$GPU "$PY" playground/dm05_so101_xbotics.py --task inference \
  --model-config.model-name-or-path "$DM05_ADAPTER" --inference-config.port "$PORT" \
  > "$OUT/server.log" 2>&1 &
server=$!
trap 'kill $server 2>/dev/null' EXIT
echo "加载 DM0.5（第一次会下载底座，要几分钟），日志 $OUT/server.log"
until curl -s -o /dev/null -m 2 "http://127.0.0.1:$PORT/"; do
  kill -0 $server 2>/dev/null || { tail -20 "$OUT/server.log"; exit 1; }
  sleep 10
done

# 推理服务返回的已是绝对关节角，所以 --action-mode absolute；写成 relative 会把状态再加一遍，
# 目标角约成两倍，不报错，只表现为成功率极低。
# 渲染放在不和别的作业共用的卡上：共用的卡可能渲出成片纯黑块，rollout 首帧自检会直接退出。
CUDA_VISIBLE_DEVICES=$GPU "$SIM_PY" script/so101/rollout_so101.py \
  --out "$OUT" --endpoint "http://127.0.0.1:$PORT/v1/infer" --label dm05 \
  --action-mode absolute --scenes "$SCENE" --episodes "$EPISODES" --no-wandb
"$SIM_PY" script/so101/make_rollout_videos.py --rollout-dir "$OUT" --out "$OUT/labeled" --per-kind 2
echo "成功率见 $OUT/rollout_dm05.json，录像在 $OUT/labeled/"
