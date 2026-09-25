#!/usr/bin/env bash
# 下载跑示例要的权重：本工作坊微调好的 DM0.5 与 DW0.5，加上 DW0.5 推理用的底座组件。
#
# DM0.5 的底座 Dexmal/DM05 不用单独下：适配器里记着它，第一次加载时自动取到 HF 缓存。
# DW0.5 的底座包 Dexmal/DW05-Robotwin 里自带一份 12 GB 的 model.pt，推理用我们微调后的权重，
# 所以这里排除它；自己从头训练时才需要它（见 05_download_training_inputs.sh）。
set -euo pipefail
source "$(dirname "$0")/00_env.sh"

hf download Harrysunshine/so101-dm05-lora-sim-real-10task --local-dir "$DM05_ADAPTER"
hf download Harrysunshine/so101-dw05-sim-real-10task --local-dir "$DW05_FINETUNED"
hf download Dexmal/DW05-Robotwin --exclude "model.pt" --local-dir "$DW05_BUNDLE"
# 扩散主干不在底座包里，放进包内约定的位置。hf download 一次只给一个 --include：
# 同一条命令给多个时实测只取回其中一部分，而且不报错。
for pattern in "*.json" "*.safetensors"; do
  hf download Wan-AI/Wan2.2-TI2V-5B --include "$pattern" --local-dir "$DW05_BUNDLE/Wan-AI/Wan2.2-TI2V-5B"
done
echo "权重就位：$SO101_WEIGHTS_DIR"
