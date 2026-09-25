# Xbotics × 原力灵机工作坊：DM0.5 策略 + DW0.5 世界模型

用同一份 SO-101 抓放数据，微调两个模型，并在仿真器里验收：

- **DM0.5（VLA 策略）**：看两路相机画面、读当前关节角、听一句指令，输出接下来 50 步动作。
- **DW0.5（动作条件世界模型）**：给它当前画面和一串动作，它画出「照这串动作做下去会看到什么」。

两个模型各自独立演示，不做闭环（世界模型的预测不回灌给策略）。

## 先看效果

DM0.5 在仿真里抓放（左顶视、右腕部，顶部横幅写明场景、局号与成败）：

| 场景 | 成功的一局 | 失败的一局 |
| --- | --- | --- |
| 4 cm 方块 | [media/dm05_cube40_success.mp4](media/dm05_cube40_success.mp4) | [media/dm05_cube40_fail.mp4](media/dm05_cube40_fail.mp4) |
| 2 cm 方块 | [media/dm05_cube20_success.mp4](media/dm05_cube20_success.mp4) | [media/dm05_cube20_fail.mp4](media/dm05_cube20_fail.mp4) |
| 罐子 | [media/dm05_cylinder40_success.mp4](media/dm05_cylinder40_success.mp4) | [media/dm05_cylinder40_fail.mp4](media/dm05_cylinder40_fail.mp4) |

DW0.5 推演未来（三行：仿真真实画面 / 按策略真实动作推演 / 按倒放的动作推演）：
[media/dw05_imagine_cube40.mp4](media/dw05_imagine_cube40.mp4) ·
[media/dw05_imagine_cube20.mp4](media/dw05_imagine_cube20.mp4) ·
[media/dw05_imagine_cylinder40.mp4](media/dw05_imagine_cylinder40.mp4)

## 用到的三个仓

| 仓 | 装什么 | 在本仓里 |
| --- | --- | --- |
| **本仓** Xbotics-Dexmal-Workshop | 示例脚本、用法、交付视频 | — |
| [dexbotic](https://github.com/Xbotics-Embodied-AI-club/dexbotic) | 把原力灵机的 VLA 工具箱与 DW0.5 世界模型合成一个框架，外加 SO-101 的数据转换、训练与评测脚本 | `third_party/dexbotic`（submodule） |
| [Xbotics-SO101-Sim](https://github.com/Xbotics-Embodied-AI-club/Xbotics-SO101-Sim) | SO-101 的 ManiSkill3 仿真器：三个抓放场景，按真机标定 | dexbotic 的仿真环境按提交号引用它 |

权重在 Hugging Face：
[Harrysunshine/so101-dm05-lora-sim-real-10task](https://huggingface.co/Harrysunshine/so101-dm05-lora-sim-real-10task)（DM0.5 LoRA 适配器）·
[Harrysunshine/so101-dw05-sim-real-10task](https://huggingface.co/Harrysunshine/so101-dw05-sim-real-10task)（DW0.5 微调权重）。

## 环境

```bash
git clone --recursive https://github.com/Xbotics-Embodied-AI-club/Xbotics-Dexmal-Workshop.git
cd Xbotics-Dexmal-Workshop/third_party/dexbotic

uv sync                          # 训练与推理侧：torch 2.11 + transformers 5.3 + deepspeed
cd script/so101/sim_env && uv sync   # 仿真侧：so101_sim + torch 2.8（驱动需支持 CUDA 12.8）
```

两边装不进同一个环境，示例脚本默认分别用 `third_party/dexbotic/.venv` 与
`third_party/dexbotic/script/so101/sim_env/.venv`，装在别处就用 `PY` / `SIM_PY` 指过去。
数据、权重与产物默认落在 `~/so101_workspace`，改 `SO101_ROOT` 即可。
另需 `hf`（Hugging Face 命令行）；自己训练时还要 `modelscope` 命令行。

显存参考：DM0.5 推理服务约 12 GB；DW0.5 推理要同时放下约 5B 参数的扩散主干和 T5 文本编码器，
建议单卡 40 GB 以上。

## 快速开始：用发布的权重跑通

```bash
bash demos/01_download_weights.sh                      # 两份微调权重 + DW0.5 底座组件
GPU=0 SCENE=cube40 bash demos/02_dm05_sim_rollout.sh   # DM0.5 在仿真里跑 5 局，出录像
GPU=0 bash demos/03_dw05_imagine.sh                    # DW0.5 按上一步的真实动作推演未来
```

- 02 的录像在 `~/so101_workspace/outputs/02_rollout/labeled/`，成功率在同目录的 `rollout_dm05.json`。
- 03 的三行对比视频与数值结论在 `~/so101_workspace/outputs/03_imagine/`。

## 完整验收与从头训练

```bash
GPUS=0,1,2 bash demos/04_dm05_eval_full.sh             # 三场景各 50 局，出 summary.json
bash demos/05_download_training_inputs.sh              # 训练数据 3698 集 + 两个底座
DM_GPUS=0,1 DW_GPUS=2,3,4 LEROBOT_PY=<装了 lerobot 的 python> bash demos/06_train.sh
```

训练配方（已在发布权重上验证）：

| | DM0.5 | DW0.5 |
| --- | --- | --- |
| 方式 | LoRA（可训参数 5.27%） | 全量微调 + DeepSpeed ZeRO-1 |
| 起点 | `Dexmal/DM05` | `Dexmal/DW05-Robotwin`，剔掉与双臂机器人绑定的动作头与本体编码器 |
| 规模 | 等效 batch 48，5000 步 | 每卡 batch 1 × 3 卡，20000 步 |
| 显存 | 4 卡时每卡约 22 GB | 3 卡时每卡约 69 GB |

每一步做什么、为什么这么做，见 [dexbotic/docs/so101.md](https://github.com/Xbotics-Embodied-AI-club/dexbotic/blob/main/docs/so101.md)。

## 验收标准与参考结果

**DM0.5**：三个仿真场景各 50 局，成败取仿真环境自带的判定（物体在料箱内、夹爪已松开、物体与机械臂都静止），
每局上限 500 步。每个场景的 Clopper-Pearson 95% 置信下界都要高于 70%，即 50 局里至少 42 局成功。

| 场景 | 发布权重的结果 | 95% 下界 |
| --- | --- | --- |
| 4 cm 方块 | 47/50 | 0.835 |
| 2 cm 方块 | 47/50 | 0.835 |
| 罐子 | 46/50 | 0.808 |

**DW0.5**：在训练集以外的仿真轨迹上，按真实动作推演的画面与真实画面的平均 PSNR，
要同时高于两个参照——「复制第一帧」（什么都不预测）和「同一串动作倒放」（给错动作）——
且逐条轨迹上真实动作胜过倒放的占多数。

| 喂给它的动作 | 发布权重的平均 PSNR（12 条轨迹） |
| --- | --- |
| 真实动作 | 21.65 dB |
| 复制第一帧 | 19.60 dB |
| 倒放的动作 | 17.60 dB |

真实动作 12 条全部胜过倒放。

## 容易踩的坑

- **动作口径。** DM0.5 按相对动作训练，但推理服务已经把当前状态加回去、返回绝对关节角。
  调仿真时用 `--action-mode absolute`；再加一次状态会让目标角约成两倍，不报错，只表现为成功率极低。
- **DW0.5 的本体状态不归一化。** 训练时状态是排布后的原始角度，推理时也要原样送入，
  不能套用底座包里 RobotWin 的归一化统计。dexbotic 的 `dw05_sim_check.py` 已经处理好。
- **共用 GPU 可能渲出黑块。** 和别的作业共用的显卡可能渲出成片纯黑像素，策略看着脏图跑，成功率被压低且不报错。
  仿真渲染放在单独的卡上；rollout 首帧会自检，纯黑像素超过 1000 就直接退出。
- **每个动作块执行 25 步再重新请求。** 同一份权重，执行 8 步就重新请求时成功率明显更低。

## 目录

```
demos/        按编号顺序跑的示例脚本（00_env.sh 是公共设置，被其余脚本 source）
media/        交付视频
third_party/  dexbotic（submodule）
```

## 许可

本仓的脚本与文档采用 Apache-2.0。DM0.5 适配器随底座 `Dexmal/DM05` 采用 Gemma 许可；
DW0.5 权重随底座 `Dexmal/DW05-Robotwin` 采用 Apache-2.0。仿真训练数据与真机数据的许可见各自数据集页面。
