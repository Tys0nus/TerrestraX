from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JointCalibration:
    direction: float = 1.0
    offset_deg: float = 90.0
    min_deg: float = 0.0
    max_deg: float = 180.0


@dataclass(frozen=True)
class StaticHardwareConfig:
    leg_id: str = "FL"
    backend: str = "arduino"
    serial_port: str = "/dev/ttyACM0"
    baudrate: int = 115200
    loop_hz: float = 50.0
    joystick_path: str = "/dev/input/js0"
    i2c_bus: int = 1
    i2c_address: int = 0x40
    pwm_hz: float = 50.0
    joint_channels: tuple[int, int, int] = (0, 1, 2)
    joint_min_pulse_us: tuple[int, int, int] = (500, 500, 500)
    joint_max_pulse_us: tuple[int, int, int] = (2500, 2500, 2500)
    servo_actuation_range_deg: float = 180.0
    coxa: JointCalibration = JointCalibration()
    femur: JointCalibration = JointCalibration()
    tibia: JointCalibration = JointCalibration()


HW_STATIC = StaticHardwareConfig()
