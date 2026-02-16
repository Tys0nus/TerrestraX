# controllers/connectors/webots_joystick.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from controller import Joystick


@dataclass
class TeleopCommand:
    vx: float = 0.0   # forward/back
    vy: float = 0.0   # left/right
    wz: float = 0.0   # yaw
    estop: bool = False


@dataclass
class JoystickState:
    axes: List[float]
    buttons: List[int]


@dataclass
class AxisMap:
    lx: int = 0
    ly: int = 1
    rx: int = 3
    ry: int = 4


@dataclass
class ButtonMap:
    estop: int = 7


@dataclass
class FilterConfig:
    deadzone: float = 0.12
    shape_exp: float = 3.0
    normalize_large_axes: bool = True  # handles [-32768, 32767] style


class WebotsJoystick:
    def __init__(
        self,
        timestep_ms: int,
        axis_map: AxisMap | None = None,
        button_map: ButtonMap | None = None,
        filt: FilterConfig | None = None,
    ):
        self.joy = Joystick()
        self.joy.enable(timestep_ms)

        self.n_axes = int(self.joy.getNumberOfAxes())
        self.n_buttons = int(self.joy.getNumberOfButtons()) if hasattr(self.joy, "getNumberOfButtons") else 0

        model = self.joy.getModel() if hasattr(self.joy, "getModel") else "unknown"
        print(f"[Joystick] model={model} axes={self.n_axes} buttons={self.n_buttons}")

        default_axis = AxisMap(ry=4 if self.n_axes > 4 else 2)
        self.axis_map = axis_map or default_axis
        self.button_map = button_map or ButtonMap()
        self.filt = filt or FilterConfig()

    @staticmethod
    def _deadzone(x: float, dz: float) -> float:
        x = float(x)
        if abs(x) < dz:
            return 0.0
        # rescale after deadzone
        return (x - dz) / (1 - dz) if x > 0 else (x + dz) / (1 - dz)

    @staticmethod
    def _signed_pow(x: float, exp: float) -> float:
        # Works for negative x and non-integer exp
        x = float(x)
        return (abs(x) ** exp) * (1.0 if x >= 0 else -1.0)

    @staticmethod
    def _clamp(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
        return max(lo, min(hi, float(x)))

    def read_state(self) -> JoystickState:
        axes = [float(self.joy.getAxisValue(i)) for i in range(self.n_axes)]

        # Optional normalization if axes look like int ranges
        if self.filt.normalize_large_axes and axes:
            m = max(abs(a) for a in axes)
            if m > 2.0:  # heuristic: not already [-1,1]
                axes = [a / m for a in axes]  # normalize by max seen that tick

        buttons: List[int] = []
        if self.n_buttons > 0 and hasattr(self.joy, "getButtonValue"):
            buttons = [int(self.joy.getButtonValue(i)) for i in range(self.n_buttons)]

        return JoystickState(axes=axes, buttons=buttons)

    def to_teleop(self, state: JoystickState) -> TeleopCommand:
        def ax(i: int) -> float:
            return state.axes[i] if 0 <= i < len(state.axes) else 0.0

        lx = self._signed_pow(self._deadzone(ax(self.axis_map.lx), self.filt.deadzone), self.filt.shape_exp)
        ly = self._signed_pow(self._deadzone(ax(self.axis_map.ly), self.filt.deadzone), self.filt.shape_exp)
        rx = self._signed_pow(self._deadzone(ax(self.axis_map.rx), self.filt.deadzone), self.filt.shape_exp)

        teleop = TeleopCommand(
            vx=self._clamp(-ly),
            vy=self._clamp(lx),
            wz=self._clamp(rx),
            estop=(
                state.buttons[self.button_map.estop] == 1
                if self.button_map.estop < len(state.buttons)
                else False
            ),
        )
        return teleop

    def read(self) -> Tuple[TeleopCommand, JoystickState]:
        state = self.read_state()
        return self.to_teleop(state), state
