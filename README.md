# Xbotics × 原力灵机工作坊：DM0.5 策略 + DW0.5 世界模型

一天的工作坊：认识 Dexbotic 框架和 SO-101 机械臂，用原力灵机开源的两个模型——
**DM0.5**（看画面、听指令、出动作的 VLA 策略）和 **DW0.5**（照一串动作画出未来画面的世界模型）——
在仿真里推理，再动手微调一次，最后把同一套代码接到真机上。

## 链接

| 用途 | 链接 |
| --- | --- |
| 讲义（PDF） | [lecture/dm05-dw05-workshop.pdf](lecture/dm05-dw05-workshop.pdf) |
| 代码（本仓） | 本仓一个 `uv sync` 装好全部依赖：模型框架 [dexbotic](https://github.com/Xbotics-Embodied-AI-club/dexbotic)、机器人接口 [LeRobot（Xbotics 维护版）](https://github.com/Xbotics-Embodied-AI-club/lerobot)，以及作为 LeRobot 依赖的仿真器 [Xbotics-SO101-Sim](https://github.com/Xbotics-Embodied-AI-club/Xbotics-SO101-Sim) |
| 权重 | [DM0.5 微调权重](https://huggingface.co/Harrysunshine/so101-dm05-lora-sim-real-10task) · [DW0.5 微调权重](https://huggingface.co/Harrysunshine/so101-dw05-sim-real-10task) |
| 数据 | [仿真数据（Hugging Face）](https://huggingface.co/datasets/Harrysunshine/so101-sim-pickplace-v2) · [真机数据（ModelScope）](https://modelscope.cn/datasets/zhuzhuangtian/so101-pick-place-tasks) |

## 第 2 节 · Dexbotic：框架与安装

需要一张 32 GB 显存的 NVIDIA 显卡（现场是 RTX 5090，驱动需支持 CUDA 12.8），以及 [uv](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/Xbotics-Embodied-AI-club/Xbotics-Dexmal-Workshop.git && cd Xbotics-Dexmal-Workshop
uv sync                                      # 一个环境装好模型框架、机器人接口与仿真器
uv run python scripts/download.py --weights   # 两份微调权重 + DW0.5 推理用的基座组件
```

数据、权重与产物默认放在 `~/so101_workspace`，设环境变量 `SO101_ROOT` 可以换位置；换了的话，下面命令里的
`~/so101_workspace` 也要换成同一个目录。以下命令都在本仓目录下运行，`uv run` 会用上面装好的那个环境。

dexbotic（模型框架）和 LeRobot（机器人接口）是面向所有人的通用包，本仓不改它们；本仓 `scripts/`
只放这次工作坊专属的脚本，推理服务与 DW0.5 推演直接用 dexbotic 自带的命令。
机器人一律用 LeRobot 的配置写法给出（`--robot.type=...`），仿真是 `so101_sim`，真机是 `so101_follower`，换机器人只换这组参数。

下面每一节对应讲义的同名章节（第 1 节是全天路线，第 9 节是小结，没有命令）；每一步为什么这样做、结果怎么读，见讲义。

## 第 3 节 · 星禾套件：SO-101 真机与仿真器

```bash
uv run python scripts/hello_robot.py --robot.type=so101_sim   # 产物 hello_robot.mp4
```

## 第 4 节 · DM0.5：原理与仿真部署

一个终端起推理服务（默认端口 7891），另一个终端跑控制循环，再给录像加标注：

```bash
uv run python -m dexbotic.so101.dm05_exp --task inference \
    --model-config.model-name-or-path ~/so101_workspace/weights/so101-dm05-lora
uv run python scripts/rollout.py --robot.type=so101_sim --robot.task=SO101PickPlaceCube40-v1 --episodes=10 --out=out/rollout
uv run python scripts/label_videos.py --rollout-dir out/rollout --out out/labeled
```

`out/rollout/rollout_dm05.json` 是成功局数，`out/labeled/` 是顶视与腕部并排、写明成败的录像
（每个场景成功、失败各取前 2 局，`--per-kind` 可改）。换场景只改 `--robot.task`，结果写进同一目录；
同一场景重跑会先清掉上一轮的录像，想留着就换 `--label` 或 `--out`。

## 第 5 节 · DW0.5：原理与仿真部署

先停掉第 4 节的推理服务，用刚才的轨迹驱动世界模型：

```bash
uv run python -m dexbotic.so101.dw05_sim_check \
    --checkpoint ~/so101_workspace/weights/so101-dw05/model.pt \
    --norm-stats ~/so101_workspace/weights/so101-dw05/norm_stats.json \
    --rollout-dir out/rollout --out out/imagine --per-scene 2
```

产物是「真实画面 / 按真实动作推演 / 按倒放动作推演」的三行对照视频与各自的 PSNR。
视频里的腕部画面有两份一样的，是模型输入格式所致，见讲义第 5.3 节。

## 第 6 节 · 数据集

```bash
uv run python scripts/download.py --data && uv run python scripts/prepare_data.py
```

## 第 7 节 · 拓展：DM0.5 单卡微调

先停掉推理服务（否则脚本会拒绝开训），一张 32 GB 的卡约 70 分钟；训完用第 300 步的检查点自动做开环自检，
结果在 `openloop.json`。然后把自己的模型部署回仿真：

```bash
uv run python scripts/train_lora.py --gpu 0
uv run python -m dexbotic.so101.dm05_exp --task inference \
    --model-config.model-name-or-path ~/so101_workspace/runs/lora_single_gpu/checkpoint-300
uv run python scripts/rollout.py --robot.type=so101_sim --robot.task=SO101PickPlaceCube40-v1 \
    --episodes=3 --label=my_lora --out=out/my_model
```

## 第 8 节 · 拓展：DM0.5 真机部署

先按讲义第 8.2 节标定。与第 4 节是同一个控制循环，只把 `--robot.*` 换成真机的那组（串口、臂的名字、两路相机）：

```bash
uv run python scripts/rollout.py \
    --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=my_so101 \
    --robot.use_degrees=true --robot.max_relative_target=5 \
    --robot.cameras="{top: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" \
    --prompt="<训练数据里的指令原句>" --episodes=3 --out=out/real
```

## 发布的模型是怎么训的

两个模型用同一份数据：仿真三个抓放场景 1498 集 + 真机遥操作九个任务 2200 集，共 3698 集、10 个任务、约 128 万帧。

| | DM0.5（策略） | DW0.5（世界模型） |
| --- | --- | --- |
| 起点 | 原力灵机的 `Dexmal/DM05` | 原力灵机的 `Dexmal/DW05-Robotwin`，去掉按双臂机器人维度排的动作头与本体编码器，这两部分从头学 |
| 方式 | LoRA（所有线性层），可训参数 324M / 6.15B = 5.27% | 全量微调，DeepSpeed ZeRO-1 |
| 等效 batch | 48 | 3 |
| 步数 | 5000 | 20000 |
| 学习率 | 1e-4，前 500 步预热，之后 cosine 衰减 | 1e-4，不预热，cosine 衰减 |
| 其他 | bf16；动作是相对当前关节角的增量，一次出 50 步 | SO-101 的 6 维状态填进原模型 16 槽的状态排布；三路视图用 顶视 + 腕部 + 腕部 |

DM0.5 每 1000 步存一次，在仿真里逐个评测：第 3000、4000 步各有一个场景没过验收线，第 5000 步三个场景都过了，发布的就是它。
第 7 节的单卡配方沿用同样的等效 batch 48，只训 300 步，用来体验流程。
完整的训练命令见 [dexbotic 的 `docs/so101.md`](https://github.com/Xbotics-Embodied-AI-club/dexbotic/blob/main/docs/so101.md)。

## 参考结果

发布的 DM0.5 用第 4 节的命令在三个仿真场景各跑 50 局：4 cm 方块 47/50、2 cm 方块 46/50、罐子 47/50。
发布的 DW0.5 在 12 条 DM0.5 跑出的仿真轨迹上（上面 50 局里每个场景的前 4 局），按真实动作推演的画面与真实画面的
平均 PSNR 为 22.97 dB，高于「复制起始帧」的 19.03 dB 和「倒放动作」的 17.33 dB，12 条全部胜过倒放。
显存峰值（与现场同代的显卡上实测）：DM0.5 推理服务约 12 GB，DW0.5 推演约 26 GB，单卡 LoRA 约 24 GB。

## 目录

```
scripts/               工作坊脚本：下载、数据转换、控制循环、录像标注、单卡微调、上手演示
lecture/               讲义（PDF）
media/                 示例视频：仿真里动一动、DM0.5 在三个场景各成功抓放一局、DW0.5 推演对照
```

## 许可

本仓的代码与文档采用 Apache-2.0。DM0.5 适配器随基座 `Dexmal/DM05` 采用 Gemma 许可；
DW0.5 权重随基座 `Dexmal/DW05-Robotwin` 采用 Apache-2.0。仿真训练数据与真机数据的许可见各自数据集页面。
