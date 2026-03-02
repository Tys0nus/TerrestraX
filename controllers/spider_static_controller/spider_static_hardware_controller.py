from __future__ import annotations

import argparse
import math
import os
import sys
import time

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from controllers.connectors.arduino_serial import ArduinoServoBridge, SerialConfig
from controllers.connectors.pca9685_i2c import PCA9685Config, PCA9685ServoBridge
from robots.config_hw_static import HW_STATIC, JointCalibration
from static_leg_common import StaticLegController

def rad_to_deg_calibrated(angle_rad: float, calib: JointCalibration) -> float:
    deg = calib.offset_deg + calib.direction * math.degrees(float(angle_rad))
    return max(calib.min_deg, min(calib.max_deg, deg))


def parse_triplet_csv(value: str) -> tuple[int, int, int]:
    chunks = [part.strip() for part in value.split(",") if part.strip()]
    if len(chunks) != 3:
        raise argparse.ArgumentTypeError("Expected exactly 3 comma-separated integers")

    try:
        parsed = tuple(int(part) for part in chunks)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Triplet values must be integers") from exc

    return parsed


def run_calibration(bridge, leg_id: str, sweep_range_deg: float, pause_s: float) -> None:
    calibrations = [HW_STATIC.coxa, HW_STATIC.femur, HW_STATIC.tibia]
    centers = [
        max(calib.min_deg, min(calib.max_deg, calib.offset_deg))
        for calib in calibrations
    ]

    print(
        f"[hardware] calibration start leg={leg_id} sweep_range={sweep_range_deg:.1f}deg pause={pause_s:.2f}s"
    )
    bridge.send_joint_degrees(leg_id, centers)
    time.sleep(max(0.0, pause_s))

    for joint_index, calib in enumerate(calibrations):
        low = max(calib.min_deg, centers[joint_index] - sweep_range_deg)
        high = min(calib.max_deg, centers[joint_index] + sweep_range_deg)

        sweep = list(centers)
        sweep[joint_index] = low
        bridge.send_joint_degrees(leg_id, sweep)
        print(f"[hardware] joint={joint_index} -> {low:.1f} deg")
        time.sleep(max(0.0, pause_s))

        sweep[joint_index] = high
        bridge.send_joint_degrees(leg_id, sweep)
        print(f"[hardware] joint={joint_index} -> {high:.1f} deg")
        time.sleep(max(0.0, pause_s))

        sweep[joint_index] = centers[joint_index]
        bridge.send_joint_degrees(leg_id, sweep)
        print(f"[hardware] joint={joint_index} -> {centers[joint_index]:.1f} deg (center)")
        time.sleep(max(0.0, pause_s))

    print("[hardware] calibration done")

def main() -> None:
    parser = argparse.ArgumentParser(description="Static leg hardware test (Arduino serial or direct PCA9685)")
    parser.add_argument(
        "--backend",
        default=HW_STATIC.backend,
        choices=["arduino", "pi-pca9685"],
        help="Actuator backend",
    )
    parser.add_argument("--port", default=HW_STATIC.serial_port, help="Arduino serial port (e.g. /dev/ttyACM0)")
    parser.add_argument("--baud", type=int, default=HW_STATIC.baudrate, help="Serial baudrate")
    parser.add_argument("--i2c-bus", type=int, default=HW_STATIC.i2c_bus, help="I2C bus index for direct PCA9685 mode")
    parser.add_argument(
        "--i2c-address",
        type=lambda value: int(value, 0),
        default=HW_STATIC.i2c_address,
        help="I2C address for PCA9685 (e.g. 0x40)",
    )
    parser.add_argument("--pwm-hz", type=float, default=HW_STATIC.pwm_hz, help="PCA9685 PWM frequency in Hz")
    parser.add_argument(
        "--channels",
        type=parse_triplet_csv,
        default=HW_STATIC.joint_channels,
        help="Servo channel triplet as coxa,femur,tibia (e.g. 0,1,2)",
    )
    parser.add_argument("--hz", type=float, default=HW_STATIC.loop_hz, help="Control loop frequency")
    parser.add_argument("--leg", default=HW_STATIC.leg_id, help="Leg ID tag sent to Arduino")
    parser.add_argument("--calibrate", action="store_true", help="Run safe per-joint calibration sweep then exit")
    parser.add_argument(
        "--calib-range-deg",
        type=float,
        default=15.0,
        help="Calibration sweep range around each joint center",
    )
    parser.add_argument("--calib-pause-s", type=float, default=0.6, help="Pause between calibration moves")
    parser.add_argument("--seconds", type=float, default=0.0, help="Run duration; 0 means run forever")
    args = parser.parse_args()

    if args.backend == "arduino":
        bridge = ArduinoServoBridge(SerialConfig(port=args.port, baudrate=args.baud))
    else:
        bridge = PCA9685ServoBridge(
            PCA9685Config(
                i2c_address=args.i2c_address,
                i2c_bus=args.i2c_bus,
                pwm_hz=args.pwm_hz,
                joint_channels=args.channels,
                min_pulse_us=HW_STATIC.joint_min_pulse_us,
                max_pulse_us=HW_STATIC.joint_max_pulse_us,
                actuation_range_deg=HW_STATIC.servo_actuation_range_deg,
            )
        )
    controller = StaticLegController()

    dt_s = 1.0 / float(args.hz)
    next_debug_t = 0.0
    wall_t0 = time.monotonic()

    if args.backend == "arduino":
        print(
            f"[hardware] static test backend={args.backend} serial={args.port} baud={args.baud} "
            f"hz={args.hz:.1f} leg={args.leg} seconds={args.seconds}"
        )
    else:
        print(
            f"[hardware] static test backend={args.backend} i2c_bus={args.i2c_bus} "
            f"i2c_address=0x{args.i2c_address:02X} pwm_hz={args.pwm_hz:.1f} channels={args.channels} "
            f"hz={args.hz:.1f} leg={args.leg} seconds={args.seconds}"
        )

    if args.calibrate:
        try:
            run_calibration(
                bridge=bridge,
                leg_id=args.leg,
                sweep_range_deg=max(0.0, float(args.calib_range_deg)),
                pause_s=max(0.0, float(args.calib_pause_s)),
            )
        except KeyboardInterrupt:
            print("[hardware] calibration interrupted")
        finally:
            bridge.close()
        return

    try:
        while True:
            loop_start = time.monotonic()
            q = controller.step(dt_s)
            angles_deg = [
                rad_to_deg_calibrated(q[0], HW_STATIC.coxa),
                rad_to_deg_calibrated(q[1], HW_STATIC.femur),
                rad_to_deg_calibrated(q[2], HW_STATIC.tibia),
            ]
            bridge.send_joint_degrees(args.leg, angles_deg)

            elapsed = loop_start - wall_t0
            if elapsed >= next_debug_t:
                print(
                    f"t={elapsed:.2f}s q=({q[0]:.3f}, {q[1]:.3f}, {q[2]:.3f}) "
                    f"deg=({angles_deg[0]:.1f}, {angles_deg[1]:.1f}, {angles_deg[2]:.1f})"
                )
                next_debug_t += 0.5

            if args.seconds > 0.0 and elapsed >= args.seconds:
                print("[hardware] duration reached, stopping")
                break

            sleep_s = dt_s - (time.monotonic() - loop_start)
            if sleep_s > 0.0:
                time.sleep(sleep_s)

    except KeyboardInterrupt:
        print("[hardware] stopping")
    finally:
        bridge.close()


if __name__ == "__main__":
    main()
