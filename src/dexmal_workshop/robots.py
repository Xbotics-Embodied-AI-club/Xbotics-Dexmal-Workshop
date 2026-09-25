"""造一台 LeRobot 机器人：仿真或真机，观测与动作的键完全相同。"""

from __future__ import annotations

#: 三个仿真场景的简称 → 注册名。
SCENES = {
    "cube40": "SO101PickPlaceCube40-v1",
    "cube20": "SO101PickPlaceCube20-v1",
    "cylinder40": "SO101PickPlaceCylinder40-v1",
}


def make_sim(scene: str, seed: int = 0, max_steps: int = 500):
    """一台由仿真扮演的 SO-101。

    Args:
        scene: `SCENES` 里的简称。
        seed: 第一局的复位种子；之后每局由控制循环调用 `reset(seed)` 换摆放。
        max_steps: 单局步数上限。

    Returns:
        已注册为 `so101_sim` 类型的 LeRobot 机器人（尚未 connect）。
    """
    import so101_sim.config_lerobot_robot  # noqa: F401  import 即注册 so101_sim 类型
    from lerobot.robots import make_robot_from_config
    from so101_sim.config_lerobot_robot import SO101SimRobotConfig

    if scene not in SCENES:
        raise ValueError(f"不认识的场景 {scene!r}；可选 {sorted(SCENES)}")
    return make_robot_from_config(
        SO101SimRobotConfig(task=SCENES[scene], seed=seed, episode_length=max_steps)
    )


def make_real(
    port: str, top_camera: str | int, wrist_camera: str | int, max_relative_target: float, robot_id: str
):
    """一台 SO-101 真机（follower 臂 + 顶视、腕部两路相机）。

    Args:
        port: follower 臂的串口，如 `/dev/ttyACM0`。
        top_camera: 顶视相机的设备号或路径。
        wrist_camera: 腕部相机的设备号或路径。
        max_relative_target: 每一步每个关节相对当前读数最多走多少（度 / 行程百分点）。
            模型第一步若给出离谱的目标，由它把手臂拦在小步里；调大前先在仿真里确认动作正常。
        robot_id: 这台臂的名字。LeRobot 按它找标定文件，必须与 `lerobot-calibrate --robot.id` 用的相同，
            否则读不到那次标定。

    Returns:
        LeRobot 的 SO-101 follower（尚未 connect）。关节读数用度，与训练数据同一口径。
    """
    from lerobot.cameras.opencv import OpenCVCameraConfig
    from lerobot.robots import make_robot_from_config
    from lerobot.robots.so_follower import SOFollowerRobotConfig

    def camera(index_or_path):
        return OpenCVCameraConfig(index_or_path=index_or_path, width=640, height=480, fps=30)

    return make_robot_from_config(
        SOFollowerRobotConfig(
            id=robot_id,
            port=port,
            cameras={"top": camera(top_camera), "wrist": camera(wrist_camera)},
            use_degrees=True,
            max_relative_target=max_relative_target,
        )
    )
