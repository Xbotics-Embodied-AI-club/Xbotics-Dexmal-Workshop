#!/usr/bin/env bash
# DM0.5 的完整仿真验收：三个场景各 50 局，判据与本工作坊的结营标准一致。
#
# 用法：GPUS=0,1,2 SIM_GPUS=0,1,2 bash demos/04_dm05_eval_full.sh [<DM0.5 权重目录>]
#   GPUS      三个推理服务各用哪张卡（每个约 12 GB 显存，可以三个挤一张卡）
#   SIM_GPUS  三个仿真进程各用哪张卡（默认同 GPUS）
#   不给权重目录就评本工作坊发布的那份；评自己训的就给 checkpoint 目录。
#
# 判据：每个场景 Clopper-Pearson 95% 置信下界都要高于 70%，即 50 局里至少 42 局成功。
# 只报点估计不够 —— 10 局 9 成的下界只有 0.555，说明不了什么。
set -euo pipefail
source "$(dirname "$0")/00_env.sh"
: "${GPUS:?用 GPUS 给出三个推理服务的卡，例如 GPUS=0,0,0}"
CKPT=${1:-$DM05_ADAPTER}
OUT=$OUTPUTS/04_eval_$(basename "$CKPT")
cd "$DEXBOTIC"

SIM_GPUS=${SIM_GPUS:-$GPUS} bash script/so101/eval_dm05_so101.sh "$CKPT" 50 "$OUT" "$GPUS"
echo "结论在 $OUT/summary.json（passed_70pct_lower_bound）"
