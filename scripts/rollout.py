"""DM0.5 驱动 SO-101 抓放：仿真与真机共用这一个控制循环。

机器人用 LeRobot 自己的配置写法给出（与 `lerobot-record` / `lerobot-calibrate` 相同），
仿真是 `so101_sim`，真机是 `so101_follower`：

    # 仿真：换 --robot.task 选场景，多次运行写进同一个 --out，结果按场景合并
    python scripts/rollout.py --robot.type=so101_sim --robot.task=SO101PickPlaceCube40-v1 \\
        --episodes=10 --out=out/rollout
    # 真机：每局之前把物体摆好，按回车开始；每局结束时由操作者判定成败
    python scripts/rollout.py --robot.type=so101_follower --robot.port=/dev/ttyACM0 \\
        --robot.id=my_so101 --robot.use_degrees=true --robot.max_relative_target=5 \\
        --robot.cameras="{top: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, \\
                          wrist: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" \\
        --prompt="Pick up a cube and place in the bin" --episodes=3 --out=out/real

`get_observation()` 给六个关节读数和两路画面，`send_action()` 收六个关节的绝对目标；
仿真与真机的差别只在 `--robot.*` 造出哪一台。

产物（`--out` 下）：
    rollout_<标签>.json          每个场景的成功局数（多次运行按场景合并）
    videos/                      逐局的顶视与腕部录像，以及逐步的关节状态与所发动作；文件格式由
                                 `dexbotic.so101.client` 定义，DW0.5 的推演（`dexbotic.so101.dw05_sim_check`）
                                 直接读这些文件。同一标签、同一场景重跑时，旧的那几局先删掉
"""

# 不加 `from __future__ import annotations`：draccus 要从注解里拿到真正的配置类，字符串注解它认不出。
import json
import pathlib
import time
from dataclasses import dataclass

import draccus
import numpy as np

# 仿真器不叫 lerobot_robot_*，LeRobot 的插件发现找不到它，靠这一行 import 完成 so101_sim 的注册。
import so101_sim.config_lerobot_robot
from dexbotic.so101.client import (
    IMAGE_SLOTS,
    SCENES,
    episode_stem,
    infer_endpoint,
    request_actions,
    save_episode,
)
from dexbotic.so101.dm05_exp import DM05InferenceConfig
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig  # noqa: F401  注册 opencv 相机
from lerobot.robots import RobotConfig, make_robot_from_config, so_follower  # noqa: F401  注册 so101_follower

#: 一块 50 步动作执行 25 步就重新请求：实测明显好于 8 步，和 50 步没有分出高下。
REPLAN = 25
#: 仿真画面里纯黑像素超过这个数就判定渲染坏了。正常渲染是 0；与别的作业共用的显卡可能渲出上万个。
SPECKLE_LIMIT = 1000
#: 单次推理请求的超时（秒）。服务正常时一次约 0.7 秒；第一次请求要预热，留足余量。
REQUEST_TIMEOUT = 120.0


@dataclass
class RolloutConfig:
    robot: RobotConfig
    #: 产物目录。
    out: str
    endpoint: str = infer_endpoint(DM05InferenceConfig.port)
    #: 写进录像与结果文件名的模型标识。
    label: str = "dm05"
    episodes: int = 10
    #: 单局步数上限。
    max_steps: int = 500
    #: 录像帧率；真机也按它下发动作，与训练数据一致。
    fps: int = 30
    #: 任务指令；仿真默认用场景自带的那句，真机必须给出训练数据里该任务的原句。
    prompt: str | None = None


def joint_state(robot, observation: dict) -> np.ndarray:
    """按机器人声明的关节顺序取出六维状态。"""
    return np.array([observation[key] for key in robot.action_features], dtype=np.float32)


def black_pixels(image) -> int:
    return int((np.asarray(image).astype(int).sum(-1) < 20).sum())


def check_robot(robot, cfg: RolloutConfig, is_sim: bool) -> None:
    """机器人口径与训练数据不一致时不报错、只会让结果安静地变差，所以开跑前逐项核对。"""
    missing = [name for name in IMAGE_SLOTS if name not in robot.observation_features]
    if missing:
        raise SystemExit(f"观测里缺少相机 {missing}：两路相机必须命名为 {list(IMAGE_SLOTS)}")
    if is_sim:
        return
    if not cfg.prompt:
        raise SystemExit("真机没有场景自带的指令，用 --prompt 给出训练数据里该任务的原句")
    if not robot.config.use_degrees:
        raise SystemExit("训练数据的关节读数单位是度：加 --robot.use_degrees=true")
    if robot.config.max_relative_target is None:
        raise SystemExit("真机请加 --robot.max_relative_target=5：模型给出离谱的目标时，手臂也只会小步移动")


def run_episode(
    robot, endpoint: str, prompt: str, max_steps: int, is_sim: bool, fps: int
) -> tuple[bool, dict]:
    """跑一局。

    Args:
        robot: 已 connect 的 LeRobot 机器人。
        endpoint: DM0.5 推理服务地址。
        prompt: 任务指令。
        max_steps: 单局步数上限。
        is_sim: 仿真每次 `send_action` 就是一步、不等墙钟，并且每步自带成败判定。
        fps: 真机下发动作的频率。

    Returns:
        `(仿真判定是否成功, 轨迹)`。真机没有自动判定，成功一项恒为 False，由调用方询问操作者。
        轨迹含逐步的两路画面、下发前的关节状态与所发的绝对动作。
    """
    observation = robot.get_observation()
    traj = {name: [np.asarray(observation[name]).copy()] for name in IMAGE_SLOTS}
    traj["state"], traj["action"] = [], []
    success, steps = False, 0
    while steps < max_steps and not success:
        state = joint_state(robot, observation)
        chunk = request_actions(endpoint, observation, state, prompt, REQUEST_TIMEOUT)
        for action in chunk[:REPLAN]:
            started = time.monotonic()
            traj["state"].append(joint_state(robot, observation))
            traj["action"].append(action)
            robot.send_action(dict(zip(robot.action_features, action.tolist(), strict=True)))
            if not is_sim:
                time.sleep(max(0.0, 1.0 / fps - (time.monotonic() - started)))
            observation = robot.get_observation()
            for name in IMAGE_SLOTS:
                traj[name].append(np.asarray(observation[name]).copy())
            steps += 1
            success = is_sim and bool(robot.last_info["is_success"])
            if success or steps >= max_steps:
                break
    return success, traj


def run(robot, cfg: RolloutConfig, scene: str, is_sim: bool, video_dir: pathlib.Path) -> dict:
    """在一个场景（或真机的一个任务）上跑完 `--episodes` 局。"""
    prompt = cfg.prompt or robot.task_description
    if is_sim:
        # 真机相机看暗处本来就会有大片黑像素，这项只查仿真渲染。
        first = robot.get_observation()
        speckle = max(black_pixels(first[name]) for name in IMAGE_SLOTS)
        if speckle > SPECKLE_LIMIT:
            raise SystemExit(f"[{scene}] 画面里有 {speckle} 个纯黑像素，是坏图；换一张不与别人共用的卡再跑")
    # 同一标签、同一场景重跑时先清掉旧的几局：否则上一轮多出来的局会留在目录里，被标注与推演一起读到。
    stale = sorted(video_dir.glob(f"{cfg.label}_{scene}_ep*"))
    for path in stale:
        path.unlink()
    if stale:
        print(f"[{scene}] 删掉上一轮留下的 {len(stale)} 个文件", flush=True)
    successes = []
    for episode in range(cfg.episodes):
        if is_sim:
            # 第 i 局用种子 seed+i 摆放物体，--robot.seed 默认 0。
            robot.reset(seed=cfg.robot.seed + episode)
        else:
            input(f"[{scene}] 第 {episode} 局：把物体摆好、手离开工作区后按回车开始（Ctrl-C 急停）")
        started = time.monotonic()
        success, traj = run_episode(robot, cfg.endpoint, prompt, cfg.max_steps, is_sim, cfg.fps)
        if not is_sim:
            success = input("这一局成功了吗？[y/N] ").strip().lower() == "y"
        successes.append(success)
        tag = "success" if success else "fail"
        stem = episode_stem(cfg.label, scene, episode, success)
        save_episode(
            video_dir, stem, traj["top"], traj["wrist"], traj["state"], traj["action"], prompt, cfg.fps
        )
        print(
            f"[{scene}] 第 {episode:3d} 局  {tag:7s} {len(traj['action']):4d} 步  "
            f"{time.monotonic() - started:5.1f}s  累计 {sum(successes)}/{len(successes)}",
            flush=True,
        )
    return {
        "episodes": len(successes),
        "successes": int(sum(successes)),
        "max_steps": cfg.max_steps,
        "prompt": prompt,
    }


@draccus.wrap()
def main(cfg: RolloutConfig) -> None:
    out = pathlib.Path(cfg.out)
    video_dir = out / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)
    is_sim = isinstance(cfg.robot, so101_sim.config_lerobot_robot.SO101SimRobotConfig)
    scene = SCENES[cfg.robot.task] if is_sim else "real"
    robot = make_robot_from_config(cfg.robot)
    check_robot(robot, cfg, is_sim)
    robot.connect()
    try:
        entry = run(robot, cfg, scene, is_sim, video_dir)
    finally:
        robot.disconnect()
    path = out / f"rollout_{cfg.label}.json"
    report = json.loads(path.read_text()) if path.is_file() else {"replan": REPLAN, "scenes": {}}
    report["scenes"][scene] = {"robot": cfg.robot.type, **entry}
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{scene}] 成功 {entry['successes']}/{entry['episodes']}  →  {path}")


if __name__ == "__main__":
    main()
