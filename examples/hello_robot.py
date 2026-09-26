"""第一次见面：用 LeRobot 造一台 SO-101，读一帧观测，让它原地挥一挥手，存下两路画面。

    # 仿真（默认 4 cm 方块场景）
    uv run python examples/hello_robot.py --robot.type=so101_sim
    # 真机：与仿真同一段代码，只换 --robot.* 这组参数（写法与 lerobot-calibrate / lerobot-record 相同）
    uv run python examples/hello_robot.py --robot.type=so101_follower --robot.port=/dev/ttyACM0 \\
        --robot.id=my_so101 --robot.use_degrees=true --robot.max_relative_target=5 \\
        --robot.cameras="{top: {type: opencv, index_or_path: 0, width: 640, height: 480, fps: 30}, \\
                          wrist: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}"

`get_observation()` 给六个关节读数（五个臂关节为度，夹爪为 0~100 行程百分比）和 `top` / `wrist`
两路画面，`send_action()` 收六个关节的绝对目标。这里让手腕左右各转 30 度、夹爪开合两次，
原地动作碰不到桌上的物体；两路画面并排存成录像。
"""

import contextlib
import time
from dataclasses import dataclass

import draccus
import imageio.v3 as iio
import numpy as np
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig  # noqa: F401  注册 opencv 相机
from lerobot.robots import RobotConfig, make_robot_from_config, so_follower  # noqa: F401  注册 so101_follower

# 仿真器把自己注册成 LeRobot 里一种叫 so101_sim 的机器人；import 这一行即完成注册。
with contextlib.suppress(ImportError):
    import so101_sim.config_lerobot_robot  # noqa: F401


@dataclass
class HelloConfig:
    robot: RobotConfig
    out: str = "hello_robot.mp4"
    #: 动作时长（秒），按 30 帧/秒下发。
    seconds: float = 3.0


@draccus.wrap()
def main(cfg: HelloConfig) -> None:
    robot = make_robot_from_config(cfg.robot)
    is_sim = hasattr(robot, "reset")
    robot.connect()
    try:
        obs = robot.get_observation()
        joints = list(robot.action_features)
        print("关节读数：", {k: round(float(obs[k]), 1) for k in joints})
        print("画面：", {k: np.asarray(obs[k]).shape for k in ("top", "wrist")})
        start = np.array([obs[k] for k in joints], dtype=float)
        steps = int(cfg.seconds * 30)
        frames = []
        for t in range(steps):
            began = time.monotonic()
            phase = np.sin(2 * np.pi * t / steps)
            target = start.copy()
            target[joints.index("wrist_roll.pos")] += 30 * phase
            target[joints.index("gripper.pos")] = 50 * abs(phase)
            robot.send_action(dict(zip(joints, target.tolist(), strict=True)))
            if not is_sim:  # 真机按 30 帧/秒的节拍下发；仿真每次 send_action 就是一步，不用等
                time.sleep(max(0.0, 1 / 30 - (time.monotonic() - began)))
            obs = robot.get_observation()
            frames.append(np.concatenate([np.asarray(obs["top"]), np.asarray(obs["wrist"])], axis=1))
        iio.imwrite(cfg.out, np.stack(frames), fps=30, codec="libx264")
        print(f"录像：{cfg.out}（左顶视、右腕部）")
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()
