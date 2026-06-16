"""Reusable driver-style gamepad bindings for Webots controllers.

Example:
    gamepad = GamepadInput(TIME_STEP)
    gamepad.bind_buttons({
        "walk": 1,
        "trot": 2,
        "estop": 10,
    })
    gamepad.bind_axes({
        "forward": "y",
        "strafe": "x",
        "turn": "x_rotation",
        "throttle": ("accelerator", "trigger"),
    })
    gamepad.bind_povs({
        "pose_up": "up",
        "pose_down": "down",
    })

    frame = gamepad.read()
    if frame.just_pressed("walk"):
        print("walk mode")
    turn_rate = frame.axis("turn")
    throttle = frame.axis("throttle")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping, Sequence

from controller import Keyboard

try:
    from .webots_joystick import AxisMap, ButtonMap, FilterConfig, JoystickState, TeleopCommand, WebotsJoystick
except ImportError:
    from webots_joystick import AxisMap, ButtonMap, FilterConfig, JoystickState, TeleopCommand, WebotsJoystick


@dataclass(frozen=True)
class AxisBinding:
    source: int | str
    invert: bool = False
    scale: float = 1.0
    mode: str = "signed"


@dataclass(frozen=True)
class PovBinding:
    direction: str


@dataclass(frozen=True)
class KeyBinding:
    keys: tuple[int, ...]


@dataclass(frozen=True)
class KeyboardAxisBinding:
    positive_keys: tuple[int, ...] = ()
    negative_keys: tuple[int, ...] = ()
    scale: float = 1.0


@dataclass
class GamepadFrame:
    teleop: TeleopCommand
    state: JoystickState
    button_bindings: Mapping[str, int]
    axis_bindings: Mapping[str, AxisBinding]
    pov_bindings: Mapping[str, PovBinding]
    key_bindings: Mapping[str, KeyBinding]
    keyboard_axis_bindings: Mapping[str, KeyboardAxisBinding]
    previous_buttons: Sequence[int] = field(default_factory=list)
    previous_pov_directions: frozenset[str] = field(default_factory=frozenset)
    current_pov_directions: frozenset[str] = field(default_factory=frozenset)
    previous_keys: frozenset[int] = field(default_factory=frozenset)
    current_keys: frozenset[int] = field(default_factory=frozenset)

    def button(self, action: str) -> bool:
        button_index = self.button_bindings.get(action)
        button_down = (
            button_index is not None
            and 0 <= button_index < len(self.state.buttons)
            and self.state.buttons[button_index] == 1
        )
        return button_down or self.key(action)

    def just_pressed(self, action: str) -> bool:
        button_index = self.button_bindings.get(action)
        current_button = (
            button_index is not None
            and 0 <= button_index < len(self.state.buttons)
            and self.state.buttons[button_index] == 1
        )
        previous_button = (
            button_index is not None
            and 0 <= button_index < len(self.previous_buttons)
            and self.previous_buttons[button_index] == 1
        )
        return (current_button and not previous_button) or self.key_just_pressed(action)

    def just_released(self, action: str) -> bool:
        button_index = self.button_bindings.get(action)
        current_button = (
            button_index is not None
            and 0 <= button_index < len(self.state.buttons)
            and self.state.buttons[button_index] == 1
        )
        previous_button = (
            button_index is not None
            and 0 <= button_index < len(self.previous_buttons)
            and self.previous_buttons[button_index] == 1
        )
        return (previous_button and not current_button) or self.key_just_released(action)

    def axis(self, action: str, default: float = 0.0) -> float:
        binding = self.axis_bindings.get(action)
        if binding is None:
            return float(default)

        value = self._axis_value(binding.source, default)
        if binding.mode == "trigger":
            value = 0.5 * (value + 1.0)
        if binding.invert:
            value = -value
        value = float(value) * float(binding.scale)

        keyboard_binding = self.keyboard_axis_bindings.get(action)
        if keyboard_binding is not None:
            value += self._keyboard_axis_value(keyboard_binding)
        return max(-1.0, min(1.0, value))

    def key(self, action: str) -> bool:
        binding = self.key_bindings.get(action)
        return binding is not None and any(key in self.current_keys for key in binding.keys)

    def key_just_pressed(self, action: str) -> bool:
        binding = self.key_bindings.get(action)
        if binding is None:
            return False
        return any(key in self.current_keys and key not in self.previous_keys for key in binding.keys)

    def key_just_released(self, action: str) -> bool:
        binding = self.key_bindings.get(action)
        if binding is None:
            return False
        return any(key not in self.current_keys and key in self.previous_keys for key in binding.keys)

    def pov(self, action: str) -> bool:
        binding = self.pov_bindings.get(action)
        return binding is not None and binding.direction in self.current_pov_directions

    def pov_just_pressed(self, action: str) -> bool:
        binding = self.pov_bindings.get(action)
        if binding is None:
            return False
        return binding.direction in self.current_pov_directions and binding.direction not in self.previous_pov_directions

    def pov_just_released(self, action: str) -> bool:
        binding = self.pov_bindings.get(action)
        if binding is None:
            return False
        return binding.direction not in self.current_pov_directions and binding.direction in self.previous_pov_directions

    def _axis_value(self, source: int | str, default: float) -> float:
        if isinstance(source, int):
            index = source
        else:
            index = GamepadInput.resolve_axis(source)

        if 0 <= index < len(self.state.axes):
            return float(self.state.axes[index])
        return float(default)

    def _keyboard_axis_value(self, binding: KeyboardAxisBinding) -> float:
        positive = any(key in self.current_keys for key in binding.positive_keys)
        negative = any(key in self.current_keys for key in binding.negative_keys)
        return float(positive - negative) * float(binding.scale)


class GamepadInput:
    AXIS_ALIASES: Dict[str, int] = {
        "x": 1,
        "y": 0,
        "left_x": 1,
        "left_y": 0,
        "y_rotation": 2,
        "x_rotation": 3,
        "right_x": 3,
        "right_y": 2,
        "accelerator": 4,
        "brake": 5,
    }
    KEY_ALIASES: Dict[str, int] = {
        "space": ord(" "),
        "esc": getattr(Keyboard, "ESCAPE", 27),
        "escape": getattr(Keyboard, "ESCAPE", 27),
        "enter": getattr(Keyboard, "ENTER", 13),
        "return": getattr(Keyboard, "ENTER", 13),
        "tab": getattr(Keyboard, "TAB", 9),
        "backspace": getattr(Keyboard, "BACKSPACE", 8),
        "delete": getattr(Keyboard, "DELETE", 127),
        "up": getattr(Keyboard, "UP", 315),
        "down": getattr(Keyboard, "DOWN", 317),
        "left": getattr(Keyboard, "LEFT", 314),
        "right": getattr(Keyboard, "RIGHT", 316),
        "home": getattr(Keyboard, "HOME", 312),
        "end": getattr(Keyboard, "END", 313),
        "pageup": getattr(Keyboard, "PAGEUP", 366),
        "pagedown": getattr(Keyboard, "PAGEDOWN", 367),
    }

    def __init__(
        self,
        timestep_ms: int,
        axis_map: AxisMap | None = None,
        button_map: ButtonMap | None = None,
        filt: FilterConfig | None = None,
        enable_keyboard: bool = False,
    ):
        self.joystick = WebotsJoystick(
            timestep_ms=timestep_ms,
            axis_map=axis_map,
            button_map=button_map,
            filt=filt,
        )
        self.keyboard = Keyboard() if enable_keyboard else None
        if self.keyboard is not None:
            self.keyboard.enable(timestep_ms)
        self._button_bindings: Dict[str, int] = {}
        self._axis_bindings: Dict[str, AxisBinding] = {}
        self._pov_bindings: Dict[str, PovBinding] = {}
        self._key_bindings: Dict[str, KeyBinding] = {}
        self._keyboard_axis_bindings: Dict[str, KeyboardAxisBinding] = {}
        self._previous_buttons: list[int] = []
        self._previous_pov_directions: frozenset[str] = frozenset()
        self._previous_keys: frozenset[int] = frozenset()

    @property
    def is_connected(self) -> bool:
        return self.joystick.is_connected

    @property
    def model(self) -> str:
        return self.joystick.model

    def bind_button(self, action: str, button_number: int) -> None:
        if button_number <= 0:
            raise ValueError("Driver button numbers are 1-based")
        self._button_bindings[action] = int(button_number) - 1

    def bind_buttons(self, bindings: Mapping[str, int]) -> None:
        for action, button_number in bindings.items():
            self.bind_button(action, button_number)

    def bind_axis(
        self,
        action: str,
        axis: int | str,
        *,
        invert: bool = False,
        scale: float = 1.0,
        mode: str = "signed",
    ) -> None:
        if mode not in {"signed", "trigger"}:
            raise ValueError("Axis binding mode must be 'signed' or 'trigger'")
        self._axis_bindings[action] = AxisBinding(source=axis, invert=invert, scale=scale, mode=mode)

    def bind_axes(self, bindings: Mapping[str, int | str | tuple[int | str, str] | AxisBinding]) -> None:
        for action, binding in bindings.items():
            if isinstance(binding, AxisBinding):
                self._axis_bindings[action] = binding
                continue
            if isinstance(binding, tuple):
                axis, mode = binding
                self.bind_axis(action, axis, mode=mode)
                continue
            self.bind_axis(action, binding)

    def bind_pov(self, action: str, direction: str) -> None:
        normalized = direction.strip().lower()
        if normalized not in {"up", "down", "left", "right"}:
            raise ValueError("POV direction must be one of: up, down, left, right")
        self._pov_bindings[action] = PovBinding(direction=normalized)

    def bind_povs(self, bindings: Mapping[str, str]) -> None:
        for action, direction in bindings.items():
            self.bind_pov(action, direction)

    def bind_key(self, action: str, key: int | str | Sequence[int | str]) -> None:
        keys = key if isinstance(key, Sequence) and not isinstance(key, str) else [key]
        self._key_bindings[action] = KeyBinding(keys=tuple(self.resolve_key(item) for item in keys))

    def bind_keys(self, bindings: Mapping[str, int | str | Sequence[int | str]]) -> None:
        for action, key in bindings.items():
            self.bind_key(action, key)

    def bind_keyboard_axis(
        self,
        action: str,
        *,
        positive: int | str | Sequence[int | str] = (),
        negative: int | str | Sequence[int | str] = (),
        scale: float = 1.0,
    ) -> None:
        self._keyboard_axis_bindings[action] = KeyboardAxisBinding(
            positive_keys=tuple(self.resolve_key(key) for key in self._as_sequence(positive)),
            negative_keys=tuple(self.resolve_key(key) for key in self._as_sequence(negative)),
            scale=float(scale),
        )

    def bind_keyboard_axes(self, bindings: Mapping[str, Mapping[str, object]]) -> None:
        for action, binding in bindings.items():
            self.bind_keyboard_axis(
                action,
                positive=binding.get("positive", ()),
                negative=binding.get("negative", ()),
                scale=float(binding.get("scale", 1.0)),
            )

    def read(self) -> GamepadFrame:
        teleop, state = self.joystick.read()
        current_pov_directions = self.decode_pov(state.povs[0] if state.povs else -1)
        current_keys = self._read_keys()
        frame = GamepadFrame(
            teleop=teleop,
            state=state,
            button_bindings=dict(self._button_bindings),
            axis_bindings=dict(self._axis_bindings),
            pov_bindings=dict(self._pov_bindings),
            key_bindings=dict(self._key_bindings),
            keyboard_axis_bindings=dict(self._keyboard_axis_bindings),
            previous_buttons=list(self._previous_buttons),
            previous_pov_directions=self._previous_pov_directions,
            current_pov_directions=current_pov_directions,
            previous_keys=self._previous_keys,
            current_keys=current_keys,
        )
        self._previous_buttons = list(state.buttons)
        self._previous_pov_directions = current_pov_directions
        self._previous_keys = current_keys
        return frame

    @classmethod
    def resolve_axis(cls, axis: int | str) -> int:
        if isinstance(axis, int):
            return int(axis)

        normalized = axis.strip().lower()
        if normalized in cls.AXIS_ALIASES:
            return cls.AXIS_ALIASES[normalized]
        if normalized.startswith("axis_"):
            return int(normalized.split("_", 1)[1])
        raise KeyError(f"Unknown axis alias: {axis}")

    @classmethod
    def resolve_key(cls, key: int | str) -> int:
        if isinstance(key, int):
            return int(key)

        normalized = key.strip().lower()
        if len(normalized) == 1:
            return ord(normalized.upper())
        if normalized in cls.KEY_ALIASES:
            return cls.KEY_ALIASES[normalized]
        if normalized.startswith("key_"):
            return int(normalized.split("_", 1)[1])
        raise KeyError(f"Unknown keyboard key alias: {key}")

    @staticmethod
    def _as_sequence(value: int | str | Sequence[int | str]) -> Sequence[int | str]:
        if isinstance(value, Sequence) and not isinstance(value, str):
            return value
        if value in (None, ""):
            return ()
        return (value,)

    def _read_keys(self) -> frozenset[int]:
        if self.keyboard is None:
            return frozenset()

        keys: set[int] = set()
        key = self.keyboard.getKey()
        while key != -1:
            keys.add(int(key))
            key = self.keyboard.getKey()
        return frozenset(keys)

    @staticmethod
    def decode_pov(pov_value: int) -> frozenset[str]:
        if pov_value < 0:
            return frozenset()

        directions: set[str] = set()
        if pov_value & 0x0001:
            directions.add("up")
        if pov_value & 0x0010:
            directions.add("down")
        if pov_value & 0x0100:
            directions.add("right")
        if pov_value & 0x1000:
            directions.add("left")
        if directions:
            return frozenset(directions)

        angle = pov_value / 100.0 if abs(pov_value) > 360 else float(pov_value)
        if angle >= 315.0 or angle < 45.0:
            directions.add("up")
        elif angle < 135.0:
            directions.add("right")
        elif angle < 225.0:
            directions.add("down")
        else:
            directions.add("left")
        return frozenset(directions)
