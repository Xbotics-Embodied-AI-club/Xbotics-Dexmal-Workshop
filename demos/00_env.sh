# 各示例脚本 source 的公共设置：dexbotic 的位置、两个环境的解释器、工作区目录。
#
# 两个环境装不进一个：仿真侧（ManiSkill / SAPIEN）钉在 torch 2.8，dexbotic 训练与推理侧
# 要 torch 2.11 + transformers 5.3，所以分开装，两边只通过 HTTP 推理服务与权重文件交接。
# 怎么装见 README「环境」一节。
#
# 工作区目录约定（数据、权重、产物各放哪）只在 dexbotic 的 script/so101/layout.py 里定义，
# 这里借它的 env.sh 拿到同一份 export，不另写一份。

DEXBOTIC=$(cd "$(dirname "${BASH_SOURCE[0]}")/../third_party/dexbotic" && pwd)
export SO101_ROOT=${SO101_ROOT:-$HOME/so101_workspace}
export PY=${PY:-$DEXBOTIC/.venv/bin/python}
export SIM_PY=${SIM_PY:-$DEXBOTIC/script/so101/sim_env/.venv/bin/python}

for interp in "$PY" "$SIM_PY"; do
  [ -x "$interp" ] || { echo "找不到解释器 $interp —— 先按 README 装好两个环境，或用 PY / SIM_PY 指过去" >&2; exit 1; }
done
source "$DEXBOTIC/script/so101/env.sh"

#: 本工作坊发布的两份微调权重，01_download_weights.sh 下载到这里。
DM05_ADAPTER=$SO101_WEIGHTS_DIR/so101-dm05-lora
DW05_FINETUNED=$SO101_WEIGHTS_DIR/so101-dw05
OUTPUTS=$SO101_ROOT/outputs
mkdir -p "$OUTPUTS"
