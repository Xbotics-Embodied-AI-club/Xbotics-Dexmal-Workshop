"""DM0.5 驱动 SO-101 抓放：仿真与真机共用这一个控制循环。

    # 仿真：三个场景各 10 局
    python -m dexmal_workshop.rollout --robot sim --scenes cube40 cube20 cylinder40 --episodes 10 --out <目录>
    # 真机：每局之前把物体摆好，按回车开始；每局结束时由操作者判定成败
    python -m dexmal_workshop.rollout --robot real --port /dev/ttyACM0 --top-camera 0 --wrist-camera 2 \\
        --prompt "Pick up a cube and place in the bin" --episodes 3 --out <目录>

机器人都经 LeRobot 的机器人接口访问：`get_observation()` 给六个关节读数和两路画面，
`send_action()` 收六个关节的绝对目标。仿真与真机的差别只在 `robots.py` 造出哪一台。

产物（`--out` 下）：
    rollout_dm05.json            每个场景的成功局数
    videos/<标签>_<场景>_ep<局号>_<success|fail>.mp4 / _wrist.mp4 / .npz
                                 逐局的顶视与腕部录像，以及逐步的关节状态与所发动作；
                                 DW0.5 的推演实验直接读这些文件
"""

from __future__ import annotations

import argparse
import json
import pathlib
import time

import numpy as np
from dexbotic.so101.client import IMAGE_SLOTS as CAMERA_ORDER
from dexbotic.so101.client import request_actions

from dexmal_workshop.robots import SCENES, make_real, make_sim

#: 一块 50 步动作执行 25 步就重新请求：实测明显好于 8 步，和 50 步没有分出高下。
REPLAN = 25
#: 纯黑像素超过这个数就判定画面是坏图。正常渲染是 0；与别的作业共用的显卡可能渲出上万个。
SPECKLE_LIMIT = 1000
#: 单次推理请求的超时（秒）。服务正常时一次约 0.7 秒；第一次请求要预热，留足余量。
REQUEST_TIMEOUT = 120.0


def joint_state(robot, observation: dict) -> np.ndarray:
    """按机器人声明的关节顺序取出六维状态。"""
    return np.array([observation[key] for key in robot.action_features], dtype=np.float32)


def black_pixels(image) -> int:
    return int((np.asarray(image).astype(int).sum(-1) < 20).sum())


def run_episode(robot, endpoint: str, prompt: str, max_steps: int, fps: float | None) -> tuple[bool, dict]:
    """跑一局。

    Args:
        robot: 已 connect 的 LeRobot 机器人。
        endpoint: DM0.5 推理服务地址。
        prompt: 任务指令。
        max_steps: 单局步数上限。
        fps: 真机按这个频率下发动作；仿真给 None，不等墙钟。

    Returns:
        `(仿真判定是否成功, 轨迹)`。真机没有自动判定，成功一项恒为 False，由调用方询问操作者。
        轨迹含逐步的两路画面、下发前的关节状态与所发的绝对动作。
    """
    observation = robot.get_observation()
    traj = {name: [np.asarray(observation[name]).copy()] for name in CAMERA_ORDER}
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
            if fps:
                time.sleep(max(0.0, 1.0 / fps - (time.monotonic() - started)))
            observation = robot.get_observation()
            for name in CAMERA_ORDER:
                traj[name].append(np.asarray(observation[name]).copy())
            steps += 1
            success = bool(getattr(robot, "last_info", {}).get("is_success", False))
            if success or steps >= max_steps:
                break
    return success, traj


def save_episode(path: pathlib.Path, traj: dict, prompt: str, fps: int) -> None:
    """存一局的两路录像与逐步状态，文件名与 DW0.5 推演实验约定的一致。"""
    import imageio.v3 as iio

    iio.imwrite(str(path.with_suffix(".mp4")), np.stack(traj["top"]), fps=fps, codec="libx264")
    iio.imwrite(
        str(path.with_name(path.name + "_wrist.mp4")), np.stack(traj["wrist"]), fps=fps, codec="libx264"
    )
    np.savez(
        path.with_suffix(".npz"),
        state=np.stack(traj["state"]),
        action=np.stack(traj["action"]),
        prompt=prompt,
    )


def run_scene(robot, args, scene: str, video_dir: pathlib.Path) -> dict:
    """在一个场景（或真机的一个任务）上跑完 `--episodes` 局。"""
    is_sim = hasattr(robot, "reset")
    prompt = args.prompt or robot.task_description
    first = robot.get_observation()
    speckle = max(black_pixels(first[name]) for name in CAMERA_ORDER)
    if speckle > SPECKLE_LIMIT:
        raise SystemExit(f"[{scene}] 画面里有 {speckle} 个纯黑像素，是坏图；换一张不与别人共用的卡再跑")
    successes = []
    for episode in range(args.episodes):
        if is_sim:
            robot.reset(seed=args.seed + episode)
        else:
            input(f"[{scene}] 第 {episode} 局：把物体摆好、手离开工作区后按回车开始（Ctrl-C 急停）")
        started = time.monotonic()
        success, traj = run_episode(
            robot, args.endpoint, prompt, args.max_steps, None if is_sim else args.fps
        )
        if not is_sim:
            success = input("这一局成功了吗？[y/N] ").strip().lower() == "y"
        successes.append(success)
        tag = "success" if success else "fail"
        save_episode(video_dir / f"{args.label}_{scene}_ep{episode:03d}_{tag}", traj, prompt, args.fps)
        print(
            f"[{scene}] 第 {episode:3d} 局  {tag:7s} {len(traj['action']):4d} 步  "
            f"{time.monotonic() - started:5.1f}s  累计 {sum(successes)}/{len(successes)}",
            flush=True,
        )
    return {"episodes": len(successes), "successes": int(sum(successes)), "prompt": prompt}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--robot", choices=["sim", "real"], default="sim")
    ap.add_argument("--out", required=True, type=pathlib.Path)
    ap.add_argument("--endpoint", default="http://127.0.0.1:7891/v1/infer")
    ap.add_argument("--label", default="dm05", help="写进录像文件名的模型标识")
    ap.add_argument("--episodes", type=int, default=10)
    ap.add_argument("--max-steps", type=int, default=500, help="单局步数上限")
    ap.add_argument("--fps", type=int, default=30, help="录像帧率；真机也按它下发动作，与训练数据一致")
    ap.add_argument("--seed", type=int, default=0, help="仿真第 i 局用 seed+i 摆放物体")
    ap.add_argument("--scenes", nargs="*", default=["cube40"], help=f"仿真场景，可选 {sorted(SCENES)}")
    ap.add_argument("--prompt", help="任务指令；仿真默认用场景自带的那句，真机必须给")
    ap.add_argument("--port", default="/dev/ttyACM0", help="真机 follower 臂的串口")
    ap.add_argument(
        "--robot-id", default="my_so101", help="真机的名字，与标定时 lerobot-calibrate --robot.id 相同"
    )
    ap.add_argument("--top-camera", default="0", help="真机顶视相机的设备号或路径")
    ap.add_argument("--wrist-camera", default="2", help="真机腕部相机的设备号或路径")
    ap.add_argument(
        "--max-relative-target", type=float, default=5.0, help="真机每步每个关节最多走多少（度 / 行程百分点）"
    )
    args = ap.parse_args()
    video_dir = args.out / "videos"
    video_dir.mkdir(parents=True, exist_ok=True)

    report = {"robot": args.robot, "replan": REPLAN, "max_steps": args.max_steps, "scenes": {}}
    if args.robot == "sim":
        for scene in args.scenes:
            robot = make_sim(scene, seed=args.seed, max_steps=args.max_steps)
            robot.connect()
            try:
                report["scenes"][scene] = run_scene(robot, args, scene, video_dir)
            finally:
                robot.disconnect()
    else:
        if not args.prompt:
            raise SystemExit("真机没有场景自带的指令，用 --prompt 给出训练数据里该任务的原句")

        def device(value: str):
            return int(value) if value.isdigit() else value

        robot = make_real(
            args.port,
            device(args.top_camera),
            device(args.wrist_camera),
            args.max_relative_target,
            args.robot_id,
        )
        robot.connect()
        try:
            report["scenes"]["real"] = run_scene(robot, args, "real", video_dir)
        finally:
            robot.disconnect()

    (args.out / "rollout_dm05.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for scene, entry in report["scenes"].items():
        print(f"[{scene}] 成功 {entry['successes']}/{entry['episodes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
