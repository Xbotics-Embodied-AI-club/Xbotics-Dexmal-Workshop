"""讲义第 3.4 节 · 第一次见面：用 LeRobot 造一台仿真 SO-101，读一帧观测，让它原地挥一挥手，存下两路画面。

    uv run python scripts/3_4_hello_robot.py --robot.type=so101_sim     # 默认 4 cm 方块场景

机器人的配置用 LeRobot 命令行的写法给出（与 lerobot-calibrate / lerobot-record 相同）。
`get_observation()` 给六个关节读数（五个臂关节为度，夹爪为 0~100 行程百分比）和 `top` / `wrist`
两路画面，`send_action()` 收六个关节的绝对目标。这里让手腕左右各转 30 度、夹爪开合两次，
原地动作碰不到桌上的物体；两路画面并排存成录像。
"""

from dataclasses import dataclass

import draccus
import imageio.v3 as iio
import numpy as np

# 仿真器把自己注册成 LeRobot 里一种叫 so101_sim 的机器人；import 这一行即完成注册。
import so101_sim.config_lerobot_robot  # noqa: F401
from lerobot.robots import RobotConfig, make_robot_from_config

#: 录像帧率，与训练数据一致。仿真每次 send_action 就是一步，不等墙钟。
FPS = 30


@dataclass
class HelloConfig:
    robot: RobotConfig
    out: str = "hello_robot.mp4"
    #: 动作时长（秒）。
    seconds: float = 3.0


@draccus.wrap()
def main(cfg: HelloConfig) -> None:
    robot = make_robot_from_config(cfg.robot)
    robot.connect()
    try:
        obs = robot.get_observation()
        joints = list(robot.action_features)
        print("关节读数：", {k: round(float(obs[k]), 1) for k in joints})
        print("画面：", {k: np.asarray(obs[k]).shape for k in ("top", "wrist")})
        start = np.array([obs[k] for k in joints], dtype=float)
        steps = int(cfg.seconds * FPS)
        frames = []
        for t in range(steps):
            phase = np.sin(2 * np.pi * t / steps)
            target = start.copy()
            target[joints.index("wrist_roll.pos")] += 30 * phase
            target[joints.index("gripper.pos")] = 50 * abs(phase)
            robot.send_action(dict(zip(joints, target.tolist(), strict=True)))
            obs = robot.get_observation()
            frames.append(np.concatenate([np.asarray(obs["top"]), np.asarray(obs["wrist"])], axis=1))
        iio.imwrite(cfg.out, np.stack(frames), fps=FPS, codec="libx264")
        print(f"录像：{cfg.out}（左顶视、右腕部）")
    finally:
        robot.disconnect()


if __name__ == "__main__":
    main()
