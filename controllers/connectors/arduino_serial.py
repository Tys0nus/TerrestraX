from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SerialConfig:
    port: str
    baudrate: int = 115200
    timeout_s: float = 0.05


class ArduinoServoBridge:
    def __init__(self, cfg: SerialConfig):
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError(
                "pyserial is required for hardware serial bridge. Install with: pip install pyserial"
            ) from exc

        self._serial = serial.Serial(port=cfg.port, baudrate=cfg.baudrate, timeout=cfg.timeout_s)

    def send_joint_degrees(self, leg_id: str, angles_deg: Iterable[float]) -> None:
        a0, a1, a2 = [float(a) for a in angles_deg]
        payload = f"SET {leg_id} {a0:.3f} {a1:.3f} {a2:.3f}\\n"
        self._serial.write(payload.encode("ascii"))
        self._serial.flush()

    def close(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()
