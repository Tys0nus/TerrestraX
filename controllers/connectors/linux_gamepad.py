from __future__ import annotations

from dataclasses import dataclass
import os
import struct


@dataclass(frozen=True)
class TeleopCommand:
    vx: float = 0.0
    vy: float = 0.0
    wz: float = 0.0
    estop: bool = False


@dataclass(frozen=True)
class AxisMap:
    lx: int = 0
    ly: int = 1
    rx: int = 3


@dataclass(frozen=True)
class ButtonMap:
    estop: int = 7


class LinuxJoystick:
    _EVENT_SIZE = 8
    _EVENT_FMT = "IhBB"
    _JS_EVENT_BUTTON = 0x01
    _JS_EVENT_AXIS = 0x02
    _JS_EVENT_INIT = 0x80

    def __init__(
        self,
        device_path: str = "/dev/input/js0",
        axis_map: AxisMap | None = None,
        button_map: ButtonMap | None = None,
        deadzone: float = 0.12,
        shape_exp: float = 3.0,
    ):
        self.axis_map = axis_map or AxisMap()
        self.button_map = button_map or ButtonMap()
        self.deadzone = float(deadzone)
        self.shape_exp = float(shape_exp)

        self.fd = os.open(device_path, os.O_RDONLY | os.O_NONBLOCK)
        self.axes: dict[int, float] = {}
        self.buttons: dict[int, int] = {}

    @staticmethod
    def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
        return max(lo, min(hi, float(x)))

    @staticmethod
    def _deadzone(x: float, dz: float) -> float:
        if abs(x) < dz:
            return 0.0
        return (x - dz) / (1.0 - dz) if x > 0.0 else (x + dz) / (1.0 - dz)

    @staticmethod
    def _signed_pow(x: float, exp: float) -> float:
        return (abs(x) ** exp) * (1.0 if x >= 0.0 else -1.0)

    def _read_events(self) -> None:
        while True:
            try:
                event = os.read(self.fd, self._EVENT_SIZE)
            except BlockingIOError:
                break

            if len(event) != self._EVENT_SIZE:
                break

            _, value, event_type, number = struct.unpack(self._EVENT_FMT, event)
            event_type = event_type & ~self._JS_EVENT_INIT

            if event_type == self._JS_EVENT_AXIS:
                self.axes[int(number)] = float(value) / 32767.0
            elif event_type == self._JS_EVENT_BUTTON:
                self.buttons[int(number)] = int(value)

    def read(self) -> TeleopCommand:
        self._read_events()

        lx = self.axes.get(self.axis_map.lx, 0.0)
        ly = self.axes.get(self.axis_map.ly, 0.0)
        rx = self.axes.get(self.axis_map.rx, 0.0)

        lx = self._signed_pow(self._deadzone(lx, self.deadzone), self.shape_exp)
        ly = self._signed_pow(self._deadzone(ly, self.deadzone), self.shape_exp)
        rx = self._signed_pow(self._deadzone(rx, self.deadzone), self.shape_exp)

        return TeleopCommand(
            vx=self._clamp(-ly),
            vy=self._clamp(lx),
            wz=self._clamp(rx),
            estop=self.buttons.get(self.button_map.estop, 0) == 1,
        )

    def close(self) -> None:
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None
