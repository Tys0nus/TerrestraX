from __future__ import annotations

import argparse
import math
import os
import sys
import time
from dataclasses import dataclass

import numpy as np
from sympy import Matrix

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from controllers.connectors.arduino_serial import ArduinoServoBridge, SerialConfig
from controllers.connectors.linux_gamepad import LinuxJoystick
from controllers.connectors.pca9685_i2c import PCA9685SpiderBridge, PCA9685SpiderConfig
from core.dtypes import IKParams
from core.inverse_kinematics import LegIK
from core.kinematics import chain_footpoint
from core.trajectory.time_laws import time_law
from robots.config_hw_spider import HW_SPIDER, JointCalibration, LegHardwareConfig
from robots.rconfig import BODY_HEIGHT, FL_chain, FR_chain, LEG_IDS, RL_chain, RR_chain


MOTOR_VELOCITY_RAD_S = 2.5
DEBUG_PERIOD_S = 0.5
TELEOP_DEADZONE = 0.12
TELEOP_BASE_FREQ_HZ = 1.0
TELEOP_STRIDE = 0.08
TELEOP_LIFT = 0.025
TELEOP_TURN = 0.07
TELEOP_STRAFE = 0.05
PREP_FOOT_INWARD_SCALE = 0.85
PREP_FOOT_LIFT_M = 0.025
PREP_LEG_DURATION_S = 0.8
PREP_LEG_ORDER = ("FL", "RR", "FR", "RL")
PREP_HEIGHT_STAGES = (0.078, 0.086, BODY_HEIGHT)
RAISE_BUTTON = 0
TELEOP_BUTTON = 1
HOLD_BUTTON = 2
ESTOP_BUTTON = 7

LEG_CHAIN_FACTORIES = {
    "FL": FL_chain,
    "FR": FR_chain,
    "RL": RL_chain,
    "RR": RR_chain,
}
LEG_PHASE_RAD = {
    "FL": 0.0,
    "FR": math.pi,
    "RL": math.pi,
    "RR": 0.0,
}
LEG_TURN_SIGN = {
    "FL": 1.0,
    "FR": -1.0,
    "RL": 1.0,
    "RR": -1.0,
}
LEG_STRAFE_SIGN = {
    "FL": 1.0,
    "FR": -1.0,
    "RL": -1.0,
    "RR": 1.0,
}


@dataclass
class LegPrepSequence:
    active: bool = False
    stage_index: int = 0
    leg_index: int = 0
    leg_start_time_s: float = 0.0


class DryRunBridge:
    def send_joint_degrees(self, leg_id: str, angles_deg) -> None:
        del leg_id, angles_deg

    def close(self) -> None:
        pass


def leg_config(leg_id: str) -> LegHardwareConfig:
    return getattr(HW_SPIDER, leg_id)


def rad_to_deg_calibrated(angle_rad: float, calib: JointCalibration) -> float:
    deg = calib.offset_deg + calib.direction * math.degrees(float(angle_rad))
    return max(calib.min_deg, min(calib.max_deg, deg))


def q_to_servo_degrees(leg_id: str, q: np.ndarray) -> list[float]:
    cfg = leg_config(leg_id)
    return [
        rad_to_deg_calibrated(float(q[0]), cfg.coxa),
        rad_to_deg_calibrated(float(q[1]), cfg.femur),
        rad_to_deg_calibrated(float(q[2]), cfg.tibia),
    ]


def send_pose(bridge, pose: dict[str, np.ndarray]) -> None:
    for leg_id in LEG_IDS:
        bridge.send_joint_degrees(leg_id, q_to_servo_degrees(leg_id, pose[leg_id]))


def copy_pose_map(source: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    return {leg_id: value.copy() for leg_id, value in source.items()}


def default_local_footpoint(leg_id: str) -> np.ndarray:
    chain = LEG_CHAIN_FACTORIES[leg_id]()
    return np.array([float(x) for x in chain_footpoint(chain, [0.0, 0.0, 0.0])], dtype=float)


def staged_local_footpoint(start_foot: np.ndarray, height: float) -> np.ndarray:
    inward_alpha = max(0.0, min(1.0, float(height) / BODY_HEIGHT))
    xy_scale = 1.0 + (PREP_FOOT_INWARD_SCALE - 1.0) * inward_alpha
    return np.array([start_foot[0] * xy_scale, start_foot[1] * xy_scale, -float(height)], dtype=float)


def swing_footpoint(start_foot: np.ndarray, target_foot: np.ndarray, s: float) -> np.ndarray:
    s = max(0.0, min(1.0, float(s)))
    point = (1.0 - s) * start_foot + s * target_foot
    point[2] += PREP_FOOT_LIFT_M * math.sin(math.pi * s)
    return point


def solve_leg_target(ik: LegIK, q_seed: np.ndarray, foot_target: np.ndarray) -> np.ndarray:
    q, info = ik.solve(
        q_seed,
        foot_target,
        IKParams(alpha=0.55, max_dq=0.2, max_iters=80, tol=1e-5),
    )
    if not info.ok:
        print(f"[hardware] IK warning err={info.err:.3e} target={foot_target}")
    return q


def apply_deadzone(value: float, deadzone: float = TELEOP_DEADZONE) -> float:
    magnitude = abs(value)
    if magnitude <= deadzone:
        return 0.0
    scaled = (magnitude - deadzone) / max(1.0 - deadzone, 1e-6)
    return math.copysign(scaled, value)


def build_teleop_pose(
    nominal_pose: dict[str, np.ndarray],
    gait_phase_rad: float,
    forward_cmd: float,
    strafe_cmd: float,
    turn_cmd: float,
) -> dict[str, np.ndarray]:
    cmd_mag = min(1.0, max(abs(forward_cmd), abs(strafe_cmd), abs(turn_cmd)))
    if cmd_mag <= 1e-6:
        return copy_pose_map(nominal_pose)

    stride = TELEOP_STRIDE * cmd_mag
    lift = TELEOP_LIFT * cmd_mag
    turn_scale = TELEOP_TURN * cmd_mag
    strafe_scale = TELEOP_STRAFE * cmd_mag
    out: dict[str, np.ndarray] = {}

    for leg_id in LEG_IDS:
        leg_phase = gait_phase_rad + LEG_PHASE_RAD[leg_id]
        swing = math.sin(leg_phase)
        lift_gate = max(0.0, swing)
        q = nominal_pose[leg_id].copy()
        q[0] += turn_scale * turn_cmd * LEG_TURN_SIGN[leg_id]
        q[0] += strafe_scale * strafe_cmd * LEG_STRAFE_SIGN[leg_id]
        q[1] += -stride * forward_cmd * swing + 0.55 * lift * lift_gate
        q[2] += 0.9 * stride * forward_cmd * swing - 1.10 * lift * lift_gate
        out[leg_id] = q

    return out


def make_bridge(args):
    if args.dry_run:
        return DryRunBridge()
    if args.backend == "arduino":
        return ArduinoServoBridge(SerialConfig(port=args.port, baudrate=args.baud))
    return PCA9685SpiderBridge(
        PCA9685SpiderConfig(
            i2c_address=args.i2c_address,
            i2c_bus=args.i2c_bus,
            pwm_hz=args.pwm_hz,
            leg_channels={leg_id: leg_config(leg_id).channels for leg_id in LEG_IDS},
            min_pulse_us=HW_SPIDER.min_pulse_us,
            max_pulse_us=HW_SPIDER.max_pulse_us,
            actuation_range_deg=HW_SPIDER.servo_actuation_range_deg,
        )
    )


def run_calibration(bridge, pause_s: float) -> None:
    print("[hardware] calibration: sending all configured offsets")
    for leg_id in LEG_IDS:
        cfg = leg_config(leg_id)
        bridge.send_joint_degrees(leg_id, [cfg.coxa.offset_deg, cfg.femur.offset_deg, cfg.tibia.offset_deg])
    time.sleep(max(0.0, pause_s))


def main() -> None:
    parser = argparse.ArgumentParser(description="Full spider hardware controller")
    parser.add_argument("--backend", default=HW_SPIDER.backend, choices=["arduino", "pi-pca9685"])
    parser.add_argument("--port", default=HW_SPIDER.serial_port)
    parser.add_argument("--baud", type=int, default=HW_SPIDER.baudrate)
    parser.add_argument("--i2c-bus", type=int, default=HW_SPIDER.i2c_bus)
    parser.add_argument("--i2c-address", type=lambda value: int(value, 0), default=HW_SPIDER.i2c_address)
    parser.add_argument("--pwm-hz", type=float, default=HW_SPIDER.pwm_hz)
    parser.add_argument("--joystick", default=HW_SPIDER.joystick_path)
    parser.add_argument("--hz", type=float, default=HW_SPIDER.loop_hz)
    parser.add_argument("--seconds", type=float, default=0.0)
    parser.add_argument("--dry-run", action="store_true", help="Run control loop without sending servo commands")
    parser.add_argument("--arm", action="store_true", help="Allow servo output; without this the controller runs dry")
    parser.add_argument("--calibrate", action="store_true", help="Send center offsets then exit")
    args = parser.parse_args()

    if not args.arm:
        args.dry_run = True
        print("[hardware] --arm not set; running dry")

    bridge = make_bridge(args)
    joystick = None
    try:
        joystick = LinuxJoystick(device_path=args.joystick)
    except (AttributeError, OSError) as exc:
        print(f"[hardware] joystick unavailable: {exc}; commands stay zero")

    leg_ik = {leg_id: LegIK(LEG_CHAIN_FACTORIES[leg_id](), T0=Matrix.eye(4)) for leg_id in LEG_IDS}
    launch_feet = {leg_id: default_local_footpoint(leg_id) for leg_id in LEG_IDS}
    stage_feet = {
        leg_id: [staged_local_footpoint(launch_feet[leg_id], height) for height in PREP_HEIGHT_STAGES]
        for leg_id in LEG_IDS
    }
    raised_pose = {
        leg_id: solve_leg_target(leg_ik[leg_id], np.zeros(3, dtype=float), stage_feet[leg_id][-1])
        for leg_id in LEG_IDS
    }
    flat_pose = {leg_id: np.zeros(3, dtype=float) for leg_id in LEG_IDS}
    current_pose = copy_pose_map(flat_pose)
    base_pose = copy_pose_map(flat_pose)
    prep = LegPrepSequence()
    raised_ready = False
    teleop_enabled = False
    gait_phase_rad = 0.0
    previous_buttons: dict[int, int] = {}

    if args.calibrate:
        try:
            run_calibration(bridge, pause_s=0.8)
        finally:
            bridge.close()
            if joystick:
                joystick.close()
        return

    dt_s = 1.0 / float(args.hz)
    start_t = time.monotonic()
    next_debug_t = 0.0
    print(
        f"[hardware] start backend={args.backend} dry_run={args.dry_run} hz={args.hz:.1f} "
        f"raise_button={RAISE_BUTTON} teleop_button={TELEOP_BUTTON} estop_button={ESTOP_BUTTON}"
    )

    try:
        while True:
            loop_t = time.monotonic()
            elapsed = loop_t - start_t
            cmd = joystick.read() if joystick else None
            buttons = dict(joystick.buttons) if joystick else {}

            def just_pressed(button: int) -> bool:
                return buttons.get(button, 0) == 1 and previous_buttons.get(button, 0) != 1

            forward_cmd = apply_deadzone(cmd.vx) if cmd else 0.0
            strafe_cmd = apply_deadzone(cmd.vy) if cmd else 0.0
            turn_cmd = apply_deadzone(cmd.wz) if cmd else 0.0

            if just_pressed(ESTOP_BUTTON) or (cmd.estop if cmd else False):
                prep.active = False
                teleop_enabled = False
                base_pose = copy_pose_map(current_pose)
                print("[hardware] estop/hold current pose")

            if just_pressed(RAISE_BUTTON) and not raised_ready:
                prep = LegPrepSequence(active=True, stage_index=0, leg_index=0, leg_start_time_s=elapsed)
                teleop_enabled = False
                base_pose = copy_pose_map(current_pose)
                print(f"[hardware] raise start stages={PREP_HEIGHT_STAGES}")

            if just_pressed(TELEOP_BUTTON) and raised_ready:
                teleop_enabled = not teleop_enabled
                gait_phase_rad = 0.0
                print(f"[hardware] teleop {'enabled' if teleop_enabled else 'disabled'}")

            if just_pressed(HOLD_BUTTON):
                prep.active = False
                teleop_enabled = False
                base_pose = copy_pose_map(current_pose)
                print("[hardware] hold current pose")

            if prep.active:
                active_leg = PREP_LEG_ORDER[prep.leg_index]
                s, _sd, _sdd = time_law(elapsed - prep.leg_start_time_s, PREP_LEG_DURATION_S)
                start_foot = launch_feet[active_leg] if prep.stage_index == 0 else stage_feet[active_leg][prep.stage_index - 1]
                target_foot = stage_feet[active_leg][prep.stage_index]
                foot_target = swing_footpoint(start_foot, target_foot, s)
                current_pose = copy_pose_map(base_pose)
                current_pose[active_leg] = solve_leg_target(leg_ik[active_leg], current_pose[active_leg], foot_target)
                if s >= 1.0:
                    current_pose[active_leg] = solve_leg_target(leg_ik[active_leg], current_pose[active_leg], target_foot)
                    base_pose[active_leg] = current_pose[active_leg].copy()
                    prep.leg_index += 1
                    prep.leg_start_time_s = elapsed
                    if prep.leg_index >= len(PREP_LEG_ORDER):
                        prep.leg_index = 0
                        prep.stage_index += 1
                        if prep.stage_index >= len(PREP_HEIGHT_STAGES):
                            prep.active = False
                            raised_ready = True
                            current_pose = copy_pose_map(raised_pose)
                            base_pose = copy_pose_map(raised_pose)
                            print("[hardware] raised stance ready")
            else:
                current_pose = copy_pose_map(base_pose)
                if teleop_enabled:
                    gait_speed = max(abs(forward_cmd), abs(strafe_cmd), abs(turn_cmd))
                    gait_phase_rad += 2.0 * math.pi * (TELEOP_BASE_FREQ_HZ + gait_speed) * dt_s
                    current_pose = build_teleop_pose(raised_pose, gait_phase_rad, forward_cmd, strafe_cmd, turn_cmd)

            send_pose(bridge, current_pose)
            previous_buttons = buttons

            if elapsed >= next_debug_t:
                mode = "teleop" if teleop_enabled else "raised" if raised_ready else "raise" if prep.active else "flat"
                print(
                    f"[hardware] t={elapsed:.2f}s mode={mode} "
                    f"cmd=({forward_cmd:+.2f},{strafe_cmd:+.2f},{turn_cmd:+.2f}) "
                    f"FL_deg={q_to_servo_degrees('FL', current_pose['FL'])}"
                )
                next_debug_t += DEBUG_PERIOD_S

            if args.seconds > 0.0 and elapsed >= args.seconds:
                break

            sleep_s = dt_s - (time.monotonic() - loop_t)
            if sleep_s > 0.0:
                time.sleep(sleep_s)
    except KeyboardInterrupt:
        print("[hardware] stopping")
    finally:
        bridge.close()
        if joystick:
            joystick.close()


if __name__ == "__main__":
    main()
