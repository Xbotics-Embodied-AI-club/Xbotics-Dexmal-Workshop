#!/bin/bash
# 工作坊主线一条龙：下权重 → 仿真里动一动 → 起 DM0.5 推理服务 → 仿真抓放 → 录像标注 → 停服务 → DW0.5 推演。
#
#     bash scripts/pipeline.sh                # 产物放 out/
#     bash scripts/pipeline.sh my_out         # 换个目录
#     EPISODES=3 TASKS="SO101PickPlaceCube40-v1 SO101PickPlaceCube20-v1" bash scripts/pipeline.sh
#
# 每一步就是讲义里那条命令，单独敲一遍效果相同；这里只是按顺序串起来，并在推演之前把推理服务停掉
# （一张 32 GB 的卡放不下两个模型）。
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=${1:-out}
EPISODES=${EPISODES:-10}
TASKS=${TASKS:-SO101PickPlaceCube40-v1}
PORT=${PORT:-7891}
mkdir -p "$OUT"

echo "== 1/6 下载发布的权重（已下过的会跳过）"
uv run python scripts/download.py --weights

echo "== 2/6 仿真里动一动"
uv run python scripts/hello_robot.py --robot.type=so101_sim --out="$OUT/hello_robot.mp4"

echo "== 3/6 起 DM0.5 推理服务（日志 $OUT/serve.log）"
uv run python scripts/serve.py --port "$PORT" > "$OUT/serve.log" 2>&1 &
SERVER=$!
trap 'kill $SERVER 2>/dev/null || true' EXIT
until curl -s -o /dev/null "http://127.0.0.1:$PORT/"; do
    kill -0 $SERVER 2>/dev/null || { echo "推理服务退出了，见 $OUT/serve.log"; tail -20 "$OUT/serve.log"; exit 1; }
    sleep 5
done

echo "== 4/6 仿真抓放：$TASKS 各 $EPISODES 局"
for task in $TASKS; do
    uv run python scripts/rollout.py --robot.type=so101_sim --robot.task="$task" \
        --episodes="$EPISODES" --endpoint="http://127.0.0.1:$PORT/v1/infer" --out="$OUT/rollout"
done

echo "== 5/6 录像标注"
uv run python scripts/label_videos.py --rollout-dir "$OUT/rollout" --out "$OUT/labeled"
kill $SERVER; wait $SERVER 2>/dev/null || true

echo "== 6/6 DW0.5 推演"
uv run python scripts/imagine.py --rollout-dir "$OUT/rollout" --out "$OUT/imagine"

echo "完成：抓放结果 $OUT/rollout/rollout_dm05.json，标注录像 $OUT/labeled/，推演对照 $OUT/imagine/"
