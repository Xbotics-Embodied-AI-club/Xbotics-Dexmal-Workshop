# Xbotics × 原力灵机工作坊：DM0.5 策略 + DW0.5 世界模型

一天的工作坊：认识 Dexbotic 框架和 SO-101 机械臂，用原力灵机开源的两个模型——
**DM0.5**（看画面、听指令、出动作的 VLA 策略）和 **DW0.5**（照一串动作画出未来画面的世界模型）——
在仿真里推理，再动手微调一次，最后把同一套代码接到真机上。

## 链接

| 用途 | 链接 |
| --- | --- |
| 讲义（PDF） | [lecture/pdf/dm05-dw05-workshop.pdf](lecture/pdf/dm05-dw05-workshop.pdf) |
| 代码（本仓） | 本仓一个 `uv sync` 装好全部依赖：模型框架 [dexbotic](https://github.com/Xbotics-Embodied-AI-club/dexbotic)、仿真器 [Xbotics-SO101-Sim](https://github.com/Xbotics-Embodied-AI-club/Xbotics-SO101-Sim)、机器人接口 [LeRobot（Xbotics 维护版）](https://github.com/Xbotics-Embodied-AI-club/lerobot) |
| 权重 | [DM0.5 微调权重](https://huggingface.co/Harrysunshine/so101-dm05-lora-sim-real-10task) · [DW0.5 微调权重](https://huggingface.co/Harrysunshine/so101-dw05-sim-real-10task) |
| 数据 | [仿真数据（Hugging Face）](https://huggingface.co/datasets/Harrysunshine/so101-sim-pickplace-v2) · [真机数据（ModelScope）](https://modelscope.cn/datasets/zhuzhuangtian/so101-pick-place-tasks) |

## 安装：三步

需要一张 32 GB 显存的 NVIDIA 显卡（现场是 RTX 5090，驱动需支持 CUDA 12.8），以及 [uv](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/Xbotics-Embodied-AI-club/Xbotics-Dexmal-Workshop.git && cd Xbotics-Dexmal-Workshop
uv sync                                                  # 一个环境装好模型、仿真器与机器人接口
uv run python scripts/download.py --weights       # 两份微调权重 + DW0.5 推理用的基座组件
```

数据、权重与产物默认放在 `~/so101_workspace`，设环境变量 `SO101_ROOT` 可以换位置。
以下命令都在本仓目录下运行；`uv run` 会用上面装好的那个环境。

分工：dexbotic（模型框架）和 LeRobot（机器人接口）是面向所有人的通用包，本仓不改它们；本仓 `scripts/`
放这次工作坊专属的脚本——下哪几份钉死版本的数据和权重、怎么转换、单卡微调配方、把 DM0.5 接到 SO-101 的
控制循环、录像标注和上手演示。推理服务与 DW0.5 推演直接用 dexbotic 自带的命令。脚本直接调用这两个包，本仓不打包安装。
机器人一律用 LeRobot 的配置写法给出（`--robot.type=...`，与 `lerobot-calibrate`、`lerobot-record` 相同），
仿真是 `so101_sim`，真机是 `so101_follower`，换机器人只换这组参数。

## 今天做什么

| 步骤 | 命令 | 产物 |
| --- | --- | --- |
| 1. 认识机械臂：仿真里动一动 | `uv run python scripts/hello_robot.py --robot.type=so101_sim` | `hello_robot.mp4` |
| 2. 起 DM0.5 推理服务（单独一个终端） | `uv run python -m dexbotic.so101.dm05_exp --task inference --model-config.model-name-or-path ~/so101_workspace/weights/so101-dm05-lora` | 服务在 `127.0.0.1:7891` |
| 3. DM0.5 在仿真里抓放 | `uv run python scripts/rollout.py --robot.type=so101_sim --robot.task=SO101PickPlaceCube40-v1 --episodes=10 --out=out/rollout` | `out/rollout/rollout_dm05.json`、逐局录像 |
| 4. 给录像加标注 | `uv run python scripts/label_videos.py --rollout-dir out/rollout --out out/labeled` | 顶视与腕部并排、写明成败的片子 |
| 5. DW0.5 推演未来（先停掉第 2 步的服务） | `uv run python -m dexbotic.so101.dw05_sim_check --checkpoint ~/so101_workspace/weights/so101-dw05/model.pt --norm-stats ~/so101_workspace/weights/so101-dw05/norm_stats.json --rollout-dir out/rollout --out out/imagine --per-scene 2` | 三行对照视频与各自的 PSNR |
| 6. 拓展：下载数据并转换 | `uv run python scripts/download.py --data && uv run python scripts/prepare_data.py` | 训练用的统一格式数据 |
| 7. 拓展：单卡 LoRA 微调（约 70 分钟，先停掉第 2 步的服务） | `uv run python scripts/train_lora.py --gpu 0` | 第 300 步检查点与开环自检 `openloop.json` |
| 7′. 拓展：部署自己训出的模型 | `uv run python -m dexbotic.so101.dm05_exp --task inference --model-config.model-name-or-path ~/so101_workspace/runs/lora_single_gpu/checkpoint-300`，再另开终端跑第 3 步的命令，加 `--label=my_lora --out=out/my_model` | 自己的模型在仿真里的录像 |
| 8. 拓展：接真机（先按讲义第 8.2 节标定） | 见下方 | 真机录像 |

第 8 步与第 3 步是同一个控制循环，只把 `--robot.*` 换成真机的那组（串口、臂的名字、两路相机）：

```bash
uv run python scripts/rollout.py \
    --robot.type=so101_follower --robot.port=/dev/ttyACM0 --robot.id=my_so101 \
    --robot.use_degrees=true --robot.max_relative_target=5 \
    --robot.cameras="{top: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" \
    --prompt="<训练数据里的指令原句>" --episodes=3 --out=out/real
```
每一步为什么这样做、结果怎么读，见讲义。

## 参考结果

发布的 DM0.5 用上面第 3 步的命令在三个仿真场景各跑 50 局：4 cm 方块 47/50、2 cm 方块 46/50、罐子 47/50。
发布的 DW0.5 在 12 条 DM0.5 跑出的仿真轨迹上（上面 50 局里每个场景的前 4 局），按真实动作推演的画面与真实画面的
平均 PSNR 为 22.97 dB，高于「复制起始帧」的 19.03 dB 和「倒放动作」的 17.33 dB，12 条全部胜过倒放。
显存峰值（与现场同代的显卡上实测）：DM0.5 推理服务约 12 GB，DW0.5 推演约 26 GB，单卡 LoRA 约 24 GB。

## 目录

```
scripts/               工作坊脚本：下载、数据转换、控制循环、录像标注、单卡微调、上手演示
lecture/               讲义源文件、PDF、出图脚本与图背后的数据
media/                 演示视频
```

## 许可

本仓的代码与文档采用 Apache-2.0。DM0.5 适配器随基座 `Dexmal/DM05` 采用 Gemma 许可；
DW0.5 权重随基座 `Dexmal/DW05-Robotwin` 采用 Apache-2.0。仿真训练数据与真机数据的许可见各自数据集页面。
