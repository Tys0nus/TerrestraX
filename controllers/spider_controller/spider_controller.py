from __future__ import annotations

import os
import sys
import math
import json
import re
from dataclasses import dataclass
from copy import deepcopy
from typing import Any

import numpy as np
from controller import Robot
from sympy import Matrix

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from controllers.connectors.gamepad import AxisBinding, GamepadInput
from core.dtypes import IKParams
from core.inverse_kinematics import LegIK
from core.kinematics import chain_footpoint
from core.trajectory.time_laws import time_law
from robots.rconfig import BODY_HEIGHT, FL_chain, FR_chain, LEG_IDS, RL_chain, RR_chain, get_q_nominal, nominal_from_height


CONTROL_BINDINGS_FILE = os.path.join(os.path.dirname(__file__), "control_bindings.json")
CONTROL_BINDINGS_ENV = "SPIDER_CONTROL_BINDINGS"
DEFAULT_CONTROL_BINDINGS: dict[str, Any] = {
    "buttons": {
        "tuck_body": 1,
        "teleop_toggle": 2,
        "hold_pose": 3,
        "estop": 10,
    },
    "keys": {
        "tuck_body": ["t"],
        "teleop_toggle": ["space"],
        "hold_pose": ["h"],
        "estop": ["escape"],
    },
    "axes": {
        "forward": {"axis": "y", "invert": True},
        "strafe": {"axis": "x"},
        "turn": {"axis": "x_rotation"},
    },
    "keyboard_axes": {
        "forward": {"positive": ["w"], "negative": ["s"]},
        "strafe": {"positive": ["d"], "negative": ["a"]},
        "turn": {"positive": ["right"], "negative": ["left"]},
    },
}
MOTOR_VELOCITY = 4.0
POSE_BLEND_S = 1.2
DEBUG_PERIOD_S = 0.5
TELEOP_DEADZONE = 0.12
TELEOP_BASE_FREQ_HZ = 1.3
TELEOP_STRIDE = 0.24
TELEOP_LIFT = 0.18
TELEOP_TURN = 0.16
TELEOP_STRAFE = 0.12
TUCK_BODY_HEIGHT_TARGET = BODY_HEIGHT
PREP_FOOT_INWARD_SCALE = 0.85
PREP_FOOT_LIFT_M = 0.025
PREP_LEG_DURATION_S = 0.65
PREP_LEG_ORDER = ("FL", "RR", "FR", "RL")
PREP_HEIGHT_STAGES = (0.078, 0.086, BODY_HEIGHT)
INDEXED_LEG_IDS = ("FL", "FR", "RL", "RR")
DUPLICATE_NAME_LEG_IDS = ("RR", "RL", "FR", "FL")
LEG_MOTOR_NAMES = {
    "FL": ("coxa_motor_FL", "femur_motor_FL", "tibia_motor_FL"),
    "FR": ("coxa_motor_FR", "femur_motor_FR", "tibia_motor_FR"),
    "RL": ("coxa_motor_RL", "femur_motor_RL", "tibia_motor_RL"),
    "RR": ("coxa_motor_RR", "femur_motor_RR", "tibia_motor_RR"),
}
LEG_CHAIN_FACTORIES = {
    "FL": FL_chain,
    "FR": FR_chain,
    "RL": RL_chain,
    "RR": RR_chain,
}

_BODY_HEIGHT_POSE_CACHE: dict[float, dict[str, np.ndarray]] = {}

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
class PoseTransition:
    active: bool = False
    start_time_s: float = 0.0
    duration_s: float = POSE_BLEND_S
    start_targets: dict[str, np.ndarray] | None = None
    target_targets: dict[str, np.ndarray] | None = None


@dataclass
class LegPrepSequence:
    active: bool = False
    stage_index: int = 0
    leg_index: int = 0
    leg_start_time_s: float = 0.0


def _deep_update(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_update(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_control_bindings() -> dict[str, Any]:
    config_path = os.environ.get(CONTROL_BINDINGS_ENV, CONTROL_BINDINGS_FILE)
    if not os.path.exists(config_path):
        return deepcopy(DEFAULT_CONTROL_BINDINGS)

    with open(config_path, "r", encoding="utf-8") as config_file:
        user_bindings = json.load(config_file)
    if not isinstance(user_bindings, dict):
        raise ValueError(f"Control binding file must contain a JSON object: {config_path}")
    return _deep_update(DEFAULT_CONTROL_BINDINGS, user_bindings)


def bind_controls(gamepad: GamepadInput, bindings: dict[str, Any]) -> None:
    gamepad.bind_buttons(bindings.get("buttons", {}))
    gamepad.bind_keys(bindings.get("keys", {}))
    gamepad.bind_keyboard_axes(bindings.get("keyboard_axes", {}))

    axis_bindings: dict[str, AxisBinding] = {}
    for action, binding in bindings.get("axes", {}).items():
        if isinstance(binding, dict):
            axis_bindings[action] = AxisBinding(
                source=binding.get("axis", action),
                invert=bool(binding.get("invert", False)),
                scale=float(binding.get("scale", 1.0)),
                mode=str(binding.get("mode", "signed")),
            )
        else:
            axis_bindings[action] = AxisBinding(source=binding)
    gamepad.bind_axes(axis_bindings)


def describe_controls(bindings: dict[str, Any]) -> str:
    rows = []
    actions = sorted(
        set(bindings.get("buttons", {}))
        | set(bindings.get("keys", {}))
        | set(bindings.get("axes", {}))
        | set(bindings.get("keyboard_axes", {}))
    )
    for action in actions:
        parts = []
        button = bindings.get("buttons", {}).get(action)
        if button is not None:
            parts.append(f"button {button}")
        keys = bindings.get("keys", {}).get(action)
        if keys:
            key_list = keys if isinstance(keys, list) else [keys]
            parts.append("key " + "/".join(str(key) for key in key_list))
        axis = bindings.get("axes", {}).get(action)
        if axis:
            axis_name = axis.get("axis") if isinstance(axis, dict) else axis
            parts.append(f"axis {axis_name}")
        keyboard_axis = bindings.get("keyboard_axes", {}).get(action)
        if keyboard_axis:
            positive = "/".join(str(key) for key in keyboard_axis.get("positive", []))
            negative = "/".join(str(key) for key in keyboard_axis.get("negative", []))
            parts.append(f"keys +{positive} -{negative}")
        rows.append(f"{action}=" + ", ".join(parts))
    return "; ".join(rows)


def _matches_device_name(name: str, base_name: str) -> bool:
    return name == base_name or name.startswith(f"{base_name}_") or name.startswith(f"{base_name}(")


def _indexed_device_number(name: str, base_name: str) -> int | None:
    match = re.fullmatch(rf"{re.escape(base_name)}_(\d+)", name)
    return int(match.group(1)) if match else None


def _duplicate_device_number(name: str, base_name: str) -> int | None:
    if name == base_name:
        return 0
    match = re.fullmatch(rf"{re.escape(base_name)}\((\d+)\)", name)
    return int(match.group(1)) if match else None


def _assign_motor_group(base_name: str, devices: list) -> dict[str, object]:
    indexed = [
        (_indexed_device_number(device.getName(), base_name), device)
        for device in devices
        if _indexed_device_number(device.getName(), base_name) is not None
    ]
    if len(indexed) >= len(LEG_IDS):
        return {
            INDEXED_LEG_IDS[index]: device
            for index, device in sorted(indexed, key=lambda item: item[0])
            if 0 <= index < len(INDEXED_LEG_IDS)
        }

    duplicate_named = [
        (_duplicate_device_number(device.getName(), base_name), device)
        for device in devices
        if _duplicate_device_number(device.getName(), base_name) is not None
    ]
    duplicate_indices = {index for index, _device in duplicate_named}
    if len(duplicate_named) >= len(LEG_IDS) and len(duplicate_indices) >= len(LEG_IDS):
        return {
            DUPLICATE_NAME_LEG_IDS[index]: device
            for index, device in sorted(duplicate_named, key=lambda item: item[0])
            if 0 <= index < len(DUPLICATE_NAME_LEG_IDS)
        }
    if len(duplicate_named) >= len(LEG_IDS):
        return {
            leg_id: device
            for leg_id, (_index, device) in zip(DUPLICATE_NAME_LEG_IDS, duplicate_named)
        }

    return {
        leg_id: device
        for leg_id, device in zip(LEG_IDS, devices)
    }


def discover_leg_motors(robot: Robot) -> dict[str, tuple]:
    explicit_motors: dict[str, tuple] = {}
    try:
        for leg_id, motor_names in LEG_MOTOR_NAMES.items():
            explicit_motors[leg_id] = tuple(robot.getDevice(name) for name in motor_names)
    except Exception:
        explicit_motors = {}
    if len(explicit_motors) == len(LEG_IDS) and all(
        all(motor is not None for motor in leg_motors)
        for leg_motors in explicit_motors.values()
    ):
        for leg_id, leg_motors in explicit_motors.items():
            print(
                f"[spider] {leg_id} motors: "
                f"{leg_motors[0].getName()}, {leg_motors[1].getName()}, {leg_motors[2].getName()}"
            )
        return explicit_motors

    motor_groups = {
        "coxa_motor": [],
        "femur_motor": [],
        "tibia_motor": [],
    }

    for device_index in range(robot.getNumberOfDevices()):
        device = robot.getDeviceByIndex(device_index)
        if device is None:
            continue

        device_name = device.getName()
        for base_name in motor_groups:
            if _matches_device_name(device_name, base_name):
                motor_groups[base_name].append(device)
                break

    if any(len(group) < len(LEG_IDS) for group in motor_groups.values()):
        discovered = ", ".join(
            f"{base_name}={len(group)}" for base_name, group in motor_groups.items()
        )
        raise RuntimeError(
            "Full robot motors not found. "
            "Expected 4 coxa, femur, and tibia motors from either the suffixed proto names "
            "or the repeated inline world names. "
            f"Discovered: {discovered}"
        )

    assigned_groups = {
        base_name: _assign_motor_group(base_name, devices)
        for base_name, devices in motor_groups.items()
    }
    missing = {
        base_name: [leg_id for leg_id in LEG_IDS if leg_id not in assigned]
        for base_name, assigned in assigned_groups.items()
    }
    missing = {base_name: legs for base_name, legs in missing.items() if legs}
    if missing:
        raise RuntimeError(f"Could not assign all leg motors: {missing}")

    for leg_id in LEG_IDS:
        print(
            f"[spider] {leg_id} motors: "
            f"{assigned_groups['coxa_motor'][leg_id].getName()}, "
            f"{assigned_groups['femur_motor'][leg_id].getName()}, "
            f"{assigned_groups['tibia_motor'][leg_id].getName()}"
        )

    return {
        leg_id: (
            assigned_groups["coxa_motor"][leg_id],
            assigned_groups["femur_motor"][leg_id],
            assigned_groups["tibia_motor"][leg_id],
        )
        for leg_id in LEG_IDS
    }


def copy_pose_map(source: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    return {leg_id: value.copy() for leg_id, value in source.items()}


def pose_for_body_height(body_height: float) -> dict[str, np.ndarray]:
    cached = _BODY_HEIGHT_POSE_CACHE.get(body_height)
    if cached is None:
        q_nominal, _feet = nominal_from_height(body_height)
        cached = {leg_id: q_nominal.copy() for leg_id in LEG_IDS}
        _BODY_HEIGHT_POSE_CACHE[body_height] = cached
    return copy_pose_map(cached)


def default_local_footpoint(leg_id: str) -> np.ndarray:
    chain = LEG_CHAIN_FACTORIES[leg_id]()
    return np.array([float(x) for x in chain_footpoint(chain, [0.0, 0.0, 0.0])], dtype=float)


def staged_local_footpoint(start_foot: np.ndarray, height: float) -> np.ndarray:
    if TUCK_BODY_HEIGHT_TARGET <= 0.0:
        inward_alpha = 1.0
    else:
        inward_alpha = max(0.0, min(1.0, float(height) / TUCK_BODY_HEIGHT_TARGET))
    xy_scale = 1.0 + (PREP_FOOT_INWARD_SCALE - 1.0) * inward_alpha
    return np.array(
        [
            float(start_foot[0]) * xy_scale,
            float(start_foot[1]) * xy_scale,
            -float(height),
        ],
        dtype=float,
    )


def swing_footpoint(start_foot: np.ndarray, target_foot: np.ndarray, s: float) -> np.ndarray:
    s = max(0.0, min(1.0, float(s)))
    point = (1.0 - s) * start_foot + s * target_foot
    point[2] += PREP_FOOT_LIFT_M * math.sin(math.pi * s)
    return point


def solve_leg_target(ik: LegIK, q_seed: np.ndarray, foot_target: np.ndarray) -> np.ndarray:
    q, info = ik.solve(
        q_seed,
        foot_target,
        IKParams(alpha=0.55, max_dq=0.25, max_iters=80, tol=1e-5),
    )
    if not info.ok:
        print(f"[spider] IK warning err={info.err:.3e} target={foot_target}")
    return q


def blend_pose_map(
    start_targets: dict[str, np.ndarray],
    target_targets: dict[str, np.ndarray],
    alpha: float,
) -> dict[str, np.ndarray]:
    alpha = max(0.0, min(1.0, float(alpha)))
    return {
        leg_id: (1.0 - alpha) * start_targets[leg_id] + alpha * target_targets[leg_id]
        for leg_id in LEG_IDS
    }


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

        # Simple model-based gait offsets around the nominal standing pose.
        q[0] += turn_scale * turn_cmd * LEG_TURN_SIGN[leg_id]
        q[0] += strafe_scale * strafe_cmd * LEG_STRAFE_SIGN[leg_id]
        q[1] += -stride * forward_cmd * swing + 0.55 * lift * lift_gate
        q[2] += 0.9 * stride * forward_cmd * swing - 1.10 * lift * lift_gate
        out[leg_id] = q

    return out


def main() -> None:
    robot = Robot()
    timestep_ms = int(robot.getBasicTimeStep())

    motors = discover_leg_motors(robot)
    for leg_motors in motors.values():
        for motor in leg_motors:
            motor.setVelocity(MOTOR_VELOCITY)
            motor.setPosition(0.0)

    control_bindings = load_control_bindings()
    gamepad = GamepadInput(timestep_ms, enable_keyboard=True)
    bind_controls(gamepad, control_bindings)

    leg_ik = {
        leg_id: LegIK(LEG_CHAIN_FACTORIES[leg_id](), T0=Matrix.eye(4))
        for leg_id in LEG_IDS
    }
    launch_feet = {
        leg_id: default_local_footpoint(leg_id)
        for leg_id in LEG_IDS
    }
    stage_feet = {
        leg_id: [
            staged_local_footpoint(launch_feet[leg_id], height)
            for height in PREP_HEIGHT_STAGES
        ]
        for leg_id in LEG_IDS
    }
    raised_q = {
        leg_id: solve_leg_target(
            leg_ik[leg_id],
            np.zeros(3, dtype=float),
            stage_feet[leg_id][-1],
        )
        for leg_id in LEG_IDS
    }

    flat_pose = {leg_id: np.zeros(3, dtype=float) for leg_id in LEG_IDS}
    body_height_pose = {leg_id: raised_q[leg_id].copy() for leg_id in LEG_IDS}
    current_targets = copy_pose_map(flat_pose)
    base_pose_targets = copy_pose_map(flat_pose)
    transition = PoseTransition()
    prep_sequence = LegPrepSequence()

    body_is_tucked = False
    teleop_enabled = False
    gait_phase_rad = 0.0
    current_cmd = (0.0, 0.0, 0.0)
    sim_time_s = 0.0
    next_debug_time_s = 0.0

    print("[spider] controller ready")
    print("[spider] motor discovery mode: dynamic device scan")
    print(f"[spider] prep height stages: {PREP_HEIGHT_STAGES}")
    print(f"[spider] FL prep foot {launch_feet['FL']} -> {stage_feet['FL'][-1]}, q={body_height_pose['FL']}")
    print(f"[spider] control bindings: {describe_controls(control_bindings)}")

    while robot.step(timestep_ms) != -1:
        dt_s = timestep_ms / 1000.0
        sim_time_s += dt_s
        frame = gamepad.read()
        forward_cmd = apply_deadzone(frame.axis("forward"))
        strafe_cmd = apply_deadzone(frame.axis("strafe"))
        turn_cmd = apply_deadzone(frame.axis("turn"))
        current_cmd = (forward_cmd, strafe_cmd, turn_cmd)

        if frame.just_pressed("estop"):
            transition.active = False
            prep_sequence.active = False
            teleop_enabled = False
            base_pose_targets = copy_pose_map(current_targets)
            body_is_tucked = all(np.allclose(base_pose_targets[leg_id], body_height_pose[leg_id]) for leg_id in LEG_IDS)
            print("[spider] estop pressed; holding current pose")

        if frame.just_pressed("tuck_body"):
            if body_is_tucked:
                print("[spider] raised stance already prepared")
            else:
                transition.active = False
                prep_sequence = LegPrepSequence(
                    active=True,
                    stage_index=0,
                    leg_index=0,
                    leg_start_time_s=sim_time_s,
                )
                body_is_tucked = False
                teleop_enabled = False
                base_pose_targets = copy_pose_map(current_targets)
                print(
                    f"[spider] preparing raised stance stages={PREP_HEIGHT_STAGES} "
                    f"legs={PREP_LEG_ORDER}"
                )

        if frame.just_pressed("teleop_toggle") and body_is_tucked:
            teleop_enabled = not teleop_enabled
            if teleop_enabled:
                gait_phase_rad = 0.0
            state_text = "enabled" if teleop_enabled else "disabled"
            print(f"[spider] teleop {state_text}")

        if frame.just_pressed("hold_pose"):
            transition.active = False
            prep_sequence.active = False
            teleop_enabled = False
            base_pose_targets = copy_pose_map(current_targets)
            body_is_tucked = all(np.allclose(base_pose_targets[leg_id], body_height_pose[leg_id]) for leg_id in LEG_IDS)
            print("[spider] holding current base pose")

        if prep_sequence.active:
            active_leg = PREP_LEG_ORDER[prep_sequence.leg_index]
            stage_index = prep_sequence.stage_index
            elapsed_s = sim_time_s - prep_sequence.leg_start_time_s
            s, _sd, _sdd = time_law(elapsed_s, PREP_LEG_DURATION_S)
            start_foot = (
                launch_feet[active_leg]
                if stage_index == 0
                else stage_feet[active_leg][stage_index - 1]
            )
            target_foot = stage_feet[active_leg][stage_index]
            foot_target = swing_footpoint(start_foot, target_foot, s)

            current_targets = copy_pose_map(base_pose_targets)
            current_targets[active_leg] = solve_leg_target(
                leg_ik[active_leg],
                current_targets[active_leg],
                foot_target,
            )

            if s >= 1.0:
                staged_q = solve_leg_target(
                    leg_ik[active_leg],
                    current_targets[active_leg],
                    target_foot,
                )
                current_targets[active_leg] = staged_q.copy()
                base_pose_targets[active_leg] = staged_q.copy()
                print(
                    f"[spider] stage {stage_index + 1}/{len(PREP_HEIGHT_STAGES)} "
                    f"{active_leg} prepared"
                )
                prep_sequence.leg_index += 1
                prep_sequence.leg_start_time_s = sim_time_s
                if prep_sequence.leg_index >= len(PREP_LEG_ORDER):
                    prep_sequence.stage_index += 1
                    prep_sequence.leg_index = 0
                    if prep_sequence.stage_index >= len(PREP_HEIGHT_STAGES):
                        prep_sequence.active = False
                        body_is_tucked = True
                        base_pose_targets = copy_pose_map(body_height_pose)
                        current_targets = copy_pose_map(body_height_pose)
                        print("[spider] raised stance prepared")
                    else:
                        next_height = PREP_HEIGHT_STAGES[prep_sequence.stage_index]
                        print(f"[spider] starting raise stage {prep_sequence.stage_index + 1}: height={next_height:.4f}m")
        elif transition.active and transition.start_targets and transition.target_targets:
            progress = (sim_time_s - transition.start_time_s) / max(transition.duration_s, 1e-6)
            current_targets = blend_pose_map(transition.start_targets, transition.target_targets, progress)
            if progress >= 1.0:
                transition.active = False
                current_targets = copy_pose_map(transition.target_targets)
                base_pose_targets = copy_pose_map(current_targets)
                body_is_tucked = all(np.allclose(base_pose_targets[leg_id], body_height_pose[leg_id]) for leg_id in LEG_IDS)
                print("[spider] tucked pose reached")
        else:
            current_targets = copy_pose_map(base_pose_targets)
            if teleop_enabled:
                gait_speed = max(abs(forward_cmd), abs(strafe_cmd), abs(turn_cmd))
                gait_phase_rad += 2.0 * math.pi * (TELEOP_BASE_FREQ_HZ + gait_speed) * dt_s
                current_targets = build_teleop_pose(
                    nominal_pose=body_height_pose,
                    gait_phase_rad=gait_phase_rad,
                    forward_cmd=forward_cmd,
                    strafe_cmd=strafe_cmd,
                    turn_cmd=turn_cmd,
                )

        for leg_id, leg_motors in motors.items():
            q = current_targets[leg_id]
            leg_motors[0].setPosition(float(q[0]))
            leg_motors[1].setPosition(float(q[1]))
            leg_motors[2].setPosition(float(q[2]))

        if sim_time_s >= next_debug_time_s:
            mode = "teleop" if teleop_enabled else "tucked" if body_is_tucked else "flat"
            if prep_sequence.active:
                mode = f"prepare_s{prep_sequence.stage_index + 1}_{PREP_LEG_ORDER[prep_sequence.leg_index]}"
            if transition.active:
                mode = "transition"
            fl_q = current_targets["FL"]
            fwd, strafe, turn = current_cmd
            print(
                f"[spider] t={sim_time_s:.2f}s mode={mode} connected={int(gamepad.is_connected)} "
                f"cmd=({fwd:+.2f},{strafe:+.2f},{turn:+.2f}) "
                f"FL=({fl_q[0]:+.3f}, {fl_q[1]:+.3f}, {fl_q[2]:+.3f})"
            )
            next_debug_time_s += DEBUG_PERIOD_S


if __name__ == "__main__":
    main()
