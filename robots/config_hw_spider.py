from __future__ import annotations

from dataclasses import dataclass

from robots.config_hw_static import JointCalibration


@dataclass(frozen=True)
class LegHardwareConfig:
    channels: tuple[int, int, int]
    coxa: JointCalibration = JointCalibration()
    femur: JointCalibration = JointCalibration()
    tibia: JointCalibration = JointCalibration()


@dataclass(frozen=True)
class SpiderHardwareConfig:
    backend: str = "pi-pca9685"
    serial_port: str = "/dev/ttyACM0"
    baudrate: int = 115200
    loop_hz: float = 50.0
    joystick_path: str = "/dev/input/js0"
    i2c_bus: int = 1
    i2c_address: int = 0x40
    pwm_hz: float = 50.0
    min_pulse_us: int = 500
    max_pulse_us: int = 2500
    servo_actuation_range_deg: float = 180.0
    FL: LegHardwareConfig = LegHardwareConfig(channels=(0, 1, 2))
    FR: LegHardwareConfig = LegHardwareConfig(channels=(3, 4, 5))
    RL: LegHardwareConfig = LegHardwareConfig(channels=(6, 7, 8))
    RR: LegHardwareConfig = LegHardwareConfig(channels=(9, 10, 11))


HW_SPIDER = SpiderHardwareConfig()
