"""第一次见面：把仿真里的 SO-101 当成一台 LeRobot 机器人，读一帧观测，让它挥一挥手。

    python -m dexmal_workshop.hello_sim

仿真与真机是同一个接口：`get_observation()` 给六个关节读数（五个臂关节为度，夹爪为 0~100
行程百分比）和 `top` / `wrist` 两路画面，`send_action()` 收六个关节的绝对目标。
这里让手腕原地左右转一个来回、夹爪开合两次（原地动作碰不到桌上的物体），把两路画面并排存成录像。
"""

from __future__ import annotations

import argparse
import pathlib

import numpy as np

from dexmal_workshop.robots import SCENES, make_sim


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scene", default="cube40", choices=sorted(SCENES))
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path("hello_sim.mp4"))
    args = ap.parse_args()

    import imageio.v3 as iio

    robot = make_sim(args.scene)
    robot.connect()
    try:
        obs = robot.get_observation()
        joints = list(robot.action_features)
        print("关节读数：", {k: round(obs[k], 1) for k in joints})
        print("画面：", {k: np.asarray(obs[k]).shape for k in ("top", "wrist")})
        print("指令：", robot.task_description)
        start = np.array([obs[k] for k in joints])
        frames = []
        # 90 步（30 fps 下 3 秒）：手腕左右各转 30 度，夹爪张开再合上。
        for t in range(90):
            phase = np.sin(2 * np.pi * t / 90)
            target = start.copy()
            target[joints.index("wrist_roll.pos")] += 30 * phase
            target[joints.index("gripper.pos")] = 50 * abs(phase)
            robot.send_action(dict(zip(joints, target.tolist(), strict=True)))
            obs = robot.get_observation()
            frames.append(np.concatenate([np.asarray(obs["top"]), np.asarray(obs["wrist"])], axis=1))
        iio.imwrite(str(args.out), np.stack(frames), fps=30, codec="libx264")
        print(f"录像：{args.out.resolve()}（左顶视、右腕部）")
    finally:
        robot.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
