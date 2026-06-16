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
    raw_buttons: List[int]
    povs: List[int]
    pressed_codes: List[int]
    mapped_pressed_codes: List[int]
    raw_axes: List[float]
    axis_starts: List[float]
    axis_mins: List[float]
    axis_maxs: List[float]
    axis_modes: List[str]


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
    DRIVER_BUTTON_TO_RAW = {
        0: 8,
        1: 9,
        2: 10,
        3: 11,
        8: 2,
        9: 3,
    }

    def __init__(
        self,
        timestep_ms: int,
        axis_map: AxisMap | None = None,
        button_map: ButtonMap | None = None,
        filt: FilterConfig | None = None,
    ):
        self.joy = Joystick()
        self.joy.enable(timestep_ms)
        self._uses_default_axis_map = axis_map is None

        self.model = ""
        self.connected = False
        self.n_axes = 0
        self.n_povs = 0
        self.button_slots = 16
        self._axis_initialized: List[bool] = []
        self._axis_starts: List[float] = []
        self._axis_mins: List[float] = []
        self._axis_maxs: List[float] = []
        self.axis_map = axis_map or self._default_axis_map(0)
        self.button_map = button_map or ButtonMap()
        self.filt = filt or FilterConfig()
        self._refresh_capabilities(announce=True)

    @staticmethod
    def _default_axis_map(axis_count: int) -> AxisMap:
        return AxisMap(lx=1, ly=0, rx=3, ry=2 if axis_count > 2 else 1)

    @property
    def is_connected(self) -> bool:
        return self.connected

    def _reset_axis_tracking(self) -> None:
        self._axis_initialized = [False] * self.n_axes
        self._axis_starts = [0.0] * self.n_axes
        self._axis_mins = [0.0] * self.n_axes
        self._axis_maxs = [0.0] * self.n_axes

    def _read_pressed_button_codes(self) -> List[int]:
        if not hasattr(self.joy, "getPressedButton"):
            return []

        pressed_codes: List[int] = []
        seen_codes: set[int] = set()
        for _ in range(64):
            code = int(self.joy.getPressedButton())
            if code < 0:
                break
            if code in seen_codes:
                break
            seen_codes.add(code)
            pressed_codes.append(code)

        if pressed_codes:
            self.button_slots = max(self.button_slots, max(pressed_codes) + 1)
        return pressed_codes

    def _refresh_capabilities(self, announce: bool = False) -> None:
        connected = bool(self.joy.isConnected()) if hasattr(self.joy, "isConnected") else False
        model = ""
        if connected and hasattr(self.joy, "getModel"):
            model = (self.joy.getModel() or "").strip()
        axis_count = int(self.joy.getNumberOfAxes()) if hasattr(self.joy, "getNumberOfAxes") else 0
        pov_count = int(self.joy.getNumberOfPovs()) if hasattr(self.joy, "getNumberOfPovs") else 0
        changed = connected != self.connected or model != self.model or axis_count != self.n_axes or pov_count != self.n_povs

        self.connected = connected
        self.model = model
        self.n_axes = axis_count
        self.n_povs = pov_count
        if changed:
            self._reset_axis_tracking()
        if self._uses_default_axis_map:
            self.axis_map = self._default_axis_map(self.n_axes)

        if changed and announce:
            state = "connected" if self.is_connected else "offline"
            model_text = self.model or "no joystick"
            print(f"[Joystick] state={state} model={model_text} axes={self.n_axes} povs={self.n_povs}")

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

    @staticmethod
    def _default_axis_span(start_value: float) -> tuple[float, float]:
        value = float(start_value)
        if -1.5 <= value <= 1.5:
            return (-1.0, 1.0)
        if 0.0 <= value <= 65535.0:
            return (0.0, 65535.0)
        if -32768.0 <= value <= 32767.0:
            return (-32768.0, 32767.0)
        extent = max(abs(value), 1.0)
        return (-extent, extent)

    @staticmethod
    def _is_centered_axis(start_value: float, lo: float, hi: float) -> bool:
        if hi <= lo:
            return True
        midpoint = 0.5 * (lo + hi)
        tolerance = 0.2 * (hi - lo)
        return abs(float(start_value) - midpoint) <= tolerance

    def _update_axis_tracking(self, raw_axes: List[float]) -> None:
        if len(raw_axes) != self.n_axes or len(self._axis_starts) != self.n_axes:
            self._reset_axis_tracking()

        for index, raw_value in enumerate(raw_axes):
            value = float(raw_value)
            if not self._axis_initialized[index]:
                self._axis_initialized[index] = True
                self._axis_starts[index] = value
                self._axis_mins[index] = value
                self._axis_maxs[index] = value
                continue

            self._axis_mins[index] = min(self._axis_mins[index], value)
            self._axis_maxs[index] = max(self._axis_maxs[index], value)

    def _normalize_axis(self, axis_index: int, raw_value: float) -> tuple[float, str]:
        value = float(raw_value)
        if abs(value) <= 2.0:
            mode = "centered" if abs(self._axis_starts[axis_index]) < 0.3 else "positive"
            return self._clamp(value), mode

        start = self._axis_starts[axis_index]
        observed_min = self._axis_mins[axis_index]
        observed_max = self._axis_maxs[axis_index]
        stick_axes = {self.axis_map.lx, self.axis_map.ly, self.axis_map.rx, self.axis_map.ry}
        if axis_index in stick_axes and abs(start) <= 512.0:
            travel = max(abs(observed_max), abs(observed_min), 32767.0)
            normalized = value / travel
            return self._clamp(normalized), "centered"

        default_min, default_max = self._default_axis_span(start if start != 0.0 else value)
        span_min = min(default_min, observed_min)
        span_max = max(default_max, observed_max)

        if self._is_centered_axis(start, span_min, span_max):
            travel = max(abs(span_max - start), abs(start - span_min), 1.0)
            normalized = (value - start) / travel
            return self._clamp(normalized), "centered"

        midpoint = 0.5 * (span_min + span_max)
        if start <= midpoint:
            travel = max(observed_max - start, 1.0)
            normalized = ((value - start) / travel) * 2.0 - 1.0
            return self._clamp(normalized), "positive"

        travel = max(start - observed_min, 1.0)
        normalized = ((start - value) / travel) * 2.0 - 1.0
        return self._clamp(normalized), "negative"

    def _remap_buttons_for_driver(self, raw_buttons: List[int]) -> tuple[List[int], List[int]]:
        if not raw_buttons:
            return [], []

        display_buttons = [0] * len(raw_buttons)
        occupied_display: set[int] = set()
        used_raw: set[int] = set()

        for display_index, raw_index in self.DRIVER_BUTTON_TO_RAW.items():
            if display_index >= len(display_buttons) or raw_index >= len(raw_buttons):
                continue
            display_buttons[display_index] = raw_buttons[raw_index]
            occupied_display.add(display_index)
            used_raw.add(raw_index)

        remaining_display = [index for index in range(len(display_buttons)) if index not in occupied_display]
        remaining_raw = [index for index in range(len(raw_buttons)) if index not in used_raw]
        for display_index, raw_index in zip(remaining_display, remaining_raw):
            display_buttons[display_index] = raw_buttons[raw_index]

        raw_to_driver = {raw_index: display_index for display_index, raw_index in self.DRIVER_BUTTON_TO_RAW.items()}
        mapped_pressed_codes = [raw_to_driver.get(raw_index, raw_index) for raw_index, pressed in enumerate(raw_buttons) if pressed == 1]
        return display_buttons, sorted(mapped_pressed_codes)

    def read_state(self) -> JoystickState:
        self._refresh_capabilities(announce=True)
        raw_axes = [float(self.joy.getAxisValue(i)) for i in range(self.n_axes)]
        self._update_axis_tracking(raw_axes)

        if self.filt.normalize_large_axes and raw_axes:
            normalized_pairs = [self._normalize_axis(index, axis) for index, axis in enumerate(raw_axes)]
            axes = [value for value, _ in normalized_pairs]
            axis_modes = [mode for _, mode in normalized_pairs]
        else:
            axes = list(raw_axes)
            axis_modes = ["raw"] * len(raw_axes)

        pressed_codes = self._read_pressed_button_codes()
        raw_buttons = [0] * self.button_slots
        for code in pressed_codes:
            if 0 <= code < len(raw_buttons):
                raw_buttons[code] = 1

        buttons, mapped_pressed_codes = self._remap_buttons_for_driver(raw_buttons)

        povs = [int(self.joy.getPovValue(i)) for i in range(self.n_povs)] if self.n_povs > 0 else []

        return JoystickState(
            axes=axes,
            buttons=buttons,
            raw_buttons=raw_buttons,
            povs=povs,
            pressed_codes=pressed_codes,
            mapped_pressed_codes=mapped_pressed_codes,
            raw_axes=raw_axes,
            axis_starts=list(self._axis_starts),
            axis_mins=list(self._axis_mins),
            axis_maxs=list(self._axis_maxs),
            axis_modes=axis_modes,
        )

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
                state.raw_buttons[self.button_map.estop] == 1
                if self.button_map.estop < len(state.raw_buttons)
                else False
            ),
        )
        return teleop

    def read(self) -> Tuple[TeleopCommand, JoystickState]:
        state = self.read_state()
        return self.to_teleop(state), state
