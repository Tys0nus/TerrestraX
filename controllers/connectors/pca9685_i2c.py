from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class PCA9685Config:
    i2c_address: int = 0x40
    i2c_bus: int = 1
    pwm_hz: float = 50.0
    joint_channels: tuple[int, int, int] = (0, 1, 2)
    min_pulse_us: tuple[int, int, int] = (500, 500, 500)
    max_pulse_us: tuple[int, int, int] = (2500, 2500, 2500)
    actuation_range_deg: float = 180.0


class PCA9685ServoBridge:
    def __init__(self, cfg: PCA9685Config):
        if len(cfg.joint_channels) != 3:
            raise ValueError("joint_channels must have exactly 3 channel indices")
        if len(cfg.min_pulse_us) != 3 or len(cfg.max_pulse_us) != 3:
            raise ValueError("pulse calibration tuples must have exactly 3 entries")

        for channel in cfg.joint_channels:
            if channel < 0 or channel > 15:
                raise ValueError(f"PCA9685 channel out of range: {channel}")

        try:
            import board
            import busio
            from adafruit_motor import servo
            from adafruit_pca9685 import PCA9685
        except ImportError as exc:
            raise RuntimeError(
                "PCA9685 backend requires Adafruit CircuitPython stack. Install with: "
                "pip install adafruit-blinka adafruit-circuitpython-pca9685 adafruit-circuitpython-motor"
            ) from exc

        if cfg.i2c_bus == 1:
            i2c = board.I2C()
        else:
            try:
                from adafruit_extended_bus import ExtendedI2C
            except ImportError as exc:
                raise RuntimeError(
                    "Non-default i2c_bus requires adafruit-extended-bus. Install with: "
                    "pip install adafruit-extended-bus"
                ) from exc
            i2c = ExtendedI2C(cfg.i2c_bus)

        self._i2c = i2c
        self._pca = PCA9685(i2c, address=int(cfg.i2c_address))
        self._pca.frequency = int(cfg.pwm_hz)

        self._servos = [
            servo.Servo(
                self._pca.channels[cfg.joint_channels[i]],
                min_pulse=cfg.min_pulse_us[i],
                max_pulse=cfg.max_pulse_us[i],
                actuation_range=float(cfg.actuation_range_deg),
            )
            for i in range(3)
        ]
        self._actuation_range_deg = float(cfg.actuation_range_deg)

    def send_joint_degrees(self, leg_id: str, angles_deg: Iterable[float]) -> None:
        del leg_id
        angles = [float(angle) for angle in angles_deg]
        if len(angles) != 3:
            raise ValueError("angles_deg must contain exactly 3 values")

        for i, angle in enumerate(angles):
            clamped = max(0.0, min(self._actuation_range_deg, angle))
            self._servos[i].angle = clamped

    def close(self) -> None:
        self._pca.deinit()
        deinit = getattr(self._i2c, "deinit", None)
        if callable(deinit):
            deinit()
