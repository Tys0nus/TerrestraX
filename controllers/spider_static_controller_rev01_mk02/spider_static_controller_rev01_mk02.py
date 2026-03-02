from __future__ import annotations

import os
import sys

from controller import Keyboard, Robot

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from controllers.connectors.hud import PoseHUD  # noqa: E402
from core.pose import LEG_POSES, ChainPose  # noqa: E402

TIME_STEP = 16

robot = Robot()
keyboard = Keyboard()
keyboard.enable(TIME_STEP)

# Get motors
j0 = robot.getDevice("coxa_motor")   # q1
j1 = robot.getDevice("femur_motor")  # q2
j2 = robot.getDevice("tibia_motor")  # q3

for m in (j0, j1, j2):
    m.setVelocity(4.0)       # rad/s
    m.setPosition(0.0)       # start straight

POSE_NAMES = list(LEG_POSES.keys()) if LEG_POSES else ["NEUTRAL"]
if not LEG_POSES:
    LEG_POSES["NEUTRAL"] = ChainPose(0.0, 0.0, 0.0)

pose_index = 0
pose_changed = True

try:
    hud = PoseHUD(robot)
    print("HUD running")
except RuntimeError as exc:
    hud = None
    print(f"HUD NOT found: {exc}")


def apply_pose(pose: ChainPose) -> None:
    j0.setPosition(pose.coxa)
    j1.setPosition(pose.femur)
    j2.setPosition(pose.tibia)


def draw_ui(pose_name: str) -> None:
    if hud:
        hud.update(pose_name)


while robot.step(TIME_STEP) != -1:
    key = keyboard.getKey()
    while key != -1:
        if key in (ord("n"), ord("N")):
            pose_index = (pose_index + 1) % len(POSE_NAMES)
            pose_changed = True
        elif key in (ord("p"), ord("P")):
            pose_index = (pose_index - 1) % len(POSE_NAMES)
            pose_changed = True
        elif ord("1") <= key <= ord("9"):
            idx = key - ord("1")
            if idx < len(POSE_NAMES):
                pose_index = idx
                pose_changed = True
        key = keyboard.getKey()

    if pose_changed:
        pose_name = POSE_NAMES[pose_index]
        apply_pose(LEG_POSES[pose_name])
        draw_ui(pose_name)
        pose_changed = False


if not hud:
    print("HUD NOT found: add a Display device named 'hud' to see UI")
