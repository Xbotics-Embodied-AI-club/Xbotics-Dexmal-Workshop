#!/usr/bin/env bash
# 自己从头训练才需要：两份训练数据，DM0.5 底座，以及 DW0.5 底座包里那份完整的 model.pt。
#
# 训练数据共 3698 集 / 10 个任务，版本钉死 —— 数据换版本，结果就不可比：
#   仿真  HF Harrysunshine/so101-sim-pickplace-v2 的 cube40 / cube20 / cylinder40，1498 集
#   真机  ModelScope zhuzhuangtian/so101-pick-place-tasks 的九个任务，2200 集
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

# hf download 一次只给一个 --include：同一条命令给多个时实测只取回其中一部分，而且不报错。
for scene in cube40 cube20 cylinder40; do
  hf download Harrysunshine/so101-sim-pickplace-v2 --repo-type dataset \
    --revision 92ca801c614cda2481029122b75ed20c72f39495 \
    --include "$scene/*" --local-dir "$SO101_DATASETS_DIR/so101-sim-640-v2"
done
modelscope download --dataset zhuzhuangtian/so101-pick-place-tasks --revision f64493c4 \
  --local_dir "$SO101_DATASETS_DIR/so101-real"

hf download Dexmal/DM05 --local-dir "$SO101_WEIGHTS_DIR/DM05"
hf download Dexmal/DW05-Robotwin --include "model.pt" --local-dir "$DW05_BUNDLE"
echo "训练输入就位；06_train.sh 开训前会逐项核对集数、帧数与视频分辨率"
