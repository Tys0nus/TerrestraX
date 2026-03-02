from __future__ import annotations

import os
import sys

from controller import Robot

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from static_leg_common import StaticLegController


robot = Robot()
TIME_STEP = int(robot.getBasicTimeStep())

def get_motor(*candidates: str):
    for name in candidates:
        motor = robot.getDevice(name)
        if motor is not None:
            return motor
    return None


# Supports both World_1.wbt (unsuffixed) and SpiderRobotStatic.proto (leg-0 suffixed)
j0 = get_motor("coxa_motor", "coxa_motor_0")
j1 = get_motor("femur_motor", "femur_motor_0")
j2 = get_motor("tibia_motor", "tibia_motor_0")

if any(m is None for m in (j0, j1, j2)):
    raise RuntimeError("Leg motors not found. Expected coxa/femur/tibia or coxa/femur/tibia with _0 suffix")

for m in (j0, j1, j2):
    m.setVelocity(4.0)
    m.setPosition(0.0)

controller = StaticLegController()
sim_t = 0.0
next_debug_t = 0.0


while robot.step(TIME_STEP) != -1:
    dt_s = TIME_STEP / 1000.0
    sim_t += dt_s
    q = controller.step(dt_s)

    j0.setPosition(float(q[0]))
    j1.setPosition(float(q[1]))
    j2.setPosition(float(q[2]))

    if sim_t >= next_debug_t:
        snap = controller.snapshot()
        print(
            f"t={sim_t:.2f}s q=({snap['q0']:.3f}, {snap['q1']:.3f}, {snap['q2']:.3f})"
        )
        next_debug_t += 0.5

