from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Sequence


@dataclass
class HudConfig:
    device_name: str = "hud"
    max_axes_shown: int = 6
    max_buttons_shown: int = 16
    stick_size: int = 92


class GamepadHUD:
    """Windows-style game controller test panel for a Webots Display."""

    BG_COLOR = 0xF4F1E8
    PANEL_COLOR = 0xFBF9F4
    FRAME_COLOR = 0x9A9384
    TEXT_COLOR = 0x1E1E1E
    MUTED_TEXT_COLOR = 0x6E6A60
    OFFLINE_COLOR = 0x8F8A81
    CONNECTED_COLOR = 0x3AA655
    ACTIVE_COLOR = 0x2EC27E
    AXIS_FILL_COLOR = 0xA1001A
    BUTTON_FILL_COLOR = 0xB31313
    BUTTON_TEXT_COLOR = 0xFFF1E8
    RAW_LINE_SPACING = 14
    POV_UP_MASK = 0x0001
    POV_DOWN_MASK = 0x0010
    POV_RIGHT_MASK = 0x0100
    POV_LEFT_MASK = 0x1000

    def __init__(self, robot, cfg: HudConfig = HudConfig()):
        self.cfg = cfg
        self.display = robot.getDevice(cfg.device_name)
        if not self.display:
            raise RuntimeError(f"HUD device '{cfg.device_name}' not found")
        self.W = self.display.getWidth()
        self.H = self.display.getHeight()

    @staticmethod
    def _clamp01(x: float) -> float:
        return max(-1.0, min(1.0, float(x)))

    @staticmethod
    def _axis_to_bar_fraction(x: float) -> float:
        return 0.5 * (GamepadHUD._clamp01(x) + 1.0)

    @staticmethod
    def _short_model(model: str) -> str:
        clean = (model or "").strip()
        if not clean:
            return "No gamepad detected"
        if len(clean) <= 28:
            return clean
        return clean[:25] + "..."

    def _axis_value(self, axes: Sequence[float], index: int) -> float:
        if 0 <= index < len(axes):
            return self._clamp01(axes[index])
        return 0.0

    @staticmethod
    def _axis_neutral(mode: str) -> float:
        return -1.0 if mode in {"positive", "negative"} else 0.0

    @staticmethod
    def _axis_mode_tag(mode: str) -> str:
        return {
            "centered": "C",
            "positive": "P",
            "negative": "N",
            "raw": "R",
        }.get(mode, "?")

    def _button_pressed(self, buttons: Sequence[int], index: int) -> bool:
        return 0 <= index < len(buttons) and int(buttons[index]) == 1

    def _draw_rect_outline(self, x: int, y: int, w: int, h: int) -> None:
        if hasattr(self.display, "drawRectangle"):
            self.display.drawRectangle(x, y, w, h)
            return
        self.display.drawLine(x, y, x + w, y)
        self.display.drawLine(x, y + h, x + w, y + h)
        self.display.drawLine(x, y, x, y + h)
        self.display.drawLine(x + w, y, x + w, y + h)

    def _fill_panel(self, x: int, y: int, w: int, h: int) -> None:
        self.display.setColor(self.PANEL_COLOR)
        self.display.fillRectangle(x, y, w, h)
        self.display.setColor(self.FRAME_COLOR)
        self._draw_rect_outline(x, y, w, h)

    def _fill_dot(self, x: int, y: int, radius: int, color: int) -> None:
        self.display.setColor(color)
        if hasattr(self.display, "fillOval"):
            self.display.fillOval(x, y, radius, radius)
        else:
            self.display.fillRectangle(x, y, radius * 2, radius * 2)

    def _draw_circle(self, x: int, y: int, radius: int, color: int) -> None:
        self.display.setColor(color)
        if hasattr(self.display, "drawOval"):
            self.display.drawOval(x, y, radius, radius)
        else:
            self._draw_rect_outline(x - radius, y - radius, radius * 2, radius * 2)

    def _draw_status(
        self,
        connected: bool,
        active: bool,
        model: str,
        seconds_since_activity: float,
        axis_count: int,
        button_count: int,
        pov_count: int,
    ) -> None:
        status_color = self.CONNECTED_COLOR if connected else self.OFFLINE_COLOR
        live_color = self.ACTIVE_COLOR if active else status_color
        status_text = "LIVE" if active else "CONNECTED" if connected else "OFFLINE"

        self._fill_dot(self.W - 188, 18, 6, live_color)
        self.display.setColor(self.TEXT_COLOR)
        self.display.drawText(status_text, self.W - 172, 10)
        self.display.setColor(self.MUTED_TEXT_COLOR)
        if connected:
            self.display.drawText(self._short_model(model), self.W - 172, 26)
            self.display.drawText(
                f"axes {axis_count}  buttons {button_count}  pov {pov_count}",
                self.W - 172,
                42,
            )
            if not active:
                self.display.drawText(f"idle {seconds_since_activity:0.1f}s", self.W - 172, 58)
        else:
            self.display.drawText("No paired controller", self.W - 172, 26)
            self.display.drawText("Focus the Webots window and press a button", self.W - 172, 42)

    def _draw_xy_test(self, x: int, y: int, x_value: float, y_value: float) -> None:
        size = min(self.cfg.stick_size, max(64, self.H - 88))
        radius = size // 2 - 12
        center_x = x + size // 2
        center_y = y + size // 2
        cursor_x = int(center_x + self._clamp01(x_value) * radius)
        cursor_y = int(center_y - self._clamp01(y_value) * radius)

        self._fill_panel(x, y, size, size)
        self.display.setColor(self.TEXT_COLOR)
        self.display.drawText("X Axis / Y Axis", x - 4, y - 16)
        self.display.drawLine(center_x, y + 8, center_x, y + size - 8)
        self.display.drawLine(x + 8, center_y, x + size - 8, center_y)
        self.display.drawText("+", center_x - 3, center_y - 5)
        self._fill_dot(cursor_x - 4, cursor_y - 4, 4, self.AXIS_FILL_COLOR)

    def _draw_axis_bar(self, x: int, y: int, w: int, h: int, label: str, value: float, neutral: float) -> None:
        self._fill_panel(x, y, w, h)
        fraction = self._axis_to_bar_fraction(value)
        neutral_fraction = self._axis_to_bar_fraction(neutral)
        left_fraction = min(fraction, neutral_fraction)
        right_fraction = max(fraction, neutral_fraction)
        inner_width = w - 6
        fill_x = x + 3 + int(inner_width * left_fraction)
        fill_width = max(2, int(inner_width * (right_fraction - left_fraction)))
        self.display.setColor(self.AXIS_FILL_COLOR)
        self.display.fillRectangle(fill_x, y + 3, fill_width, h - 6)
        marker_x = x + 3 + int(inner_width * neutral_fraction)
        self.display.setColor(self.FRAME_COLOR)
        self.display.drawLine(marker_x, y + 2, marker_x, y + h - 2)
        self.display.setColor(self.TEXT_COLOR)
        self.display.drawText(f"{label} {value:+.2f}", x + w + 8, y - 2)

    def _draw_buttons_panel(self, x: int, y: int, buttons: Sequence[int], button_base: int) -> None:
        panel_w = 230
        panel_h = 68
        self._fill_panel(x, y, panel_w, panel_h)
        self.display.setColor(self.TEXT_COLOR)
        self.display.drawText("Buttons", x + 8, y - 16)

        radius = 6
        col_gap = 26
        row_gap = 26
        count = min(max(self.cfg.max_buttons_shown, len(buttons)), self.cfg.max_buttons_shown)
        for index in range(count):
            row = index // 8
            col = index % 8
            cx = x + 12 + col * col_gap
            cy = y + 18 + row * row_gap
            pressed = self._button_pressed(buttons, index)
            self.display.setColor(self.BUTTON_FILL_COLOR if pressed else self.PANEL_COLOR)
            if hasattr(self.display, "fillOval"):
                self.display.fillOval(cx, cy, radius, radius)
            else:
                self.display.fillRectangle(cx - radius, cy - radius, radius * 2, radius * 2)
            self._draw_circle(cx, cy, radius, 0x000000)
            self.display.setColor(self.BUTTON_TEXT_COLOR if pressed else self.TEXT_COLOR)
            self.display.drawText(str(index + 1 + button_base), cx - 4, cy - 4)

    def _decode_pov(self, pov_value: int) -> set[str]:
        if pov_value < 0:
            return set()

        directions: set[str] = set()
        if pov_value & self.POV_UP_MASK:
            directions.add("up")
        if pov_value & self.POV_DOWN_MASK:
            directions.add("down")
        if pov_value & self.POV_RIGHT_MASK:
            directions.add("right")
        if pov_value & self.POV_LEFT_MASK:
            directions.add("left")
        if directions:
            return directions

        angle = pov_value / 100.0 if abs(pov_value) > 360 else float(pov_value)
        if angle >= 315.0 or angle < 45.0:
            directions.add("up")
        elif angle < 135.0:
            directions.add("right")
        elif angle < 225.0:
            directions.add("down")
        else:
            directions.add("left")
        return directions

    def _draw_pov_hat(self, x: int, y: int, pov_value: int) -> None:
        panel_w = 88
        panel_h = 68
        center_x = x + panel_w // 2
        center_y = y + panel_h // 2
        self._fill_panel(x, y, panel_w, panel_h)
        self.display.setColor(self.TEXT_COLOR)
        self.display.drawText("Point of View Hat", x + 4, y - 16)

        directions = self._decode_pov(pov_value)
        button_size = 14
        positions = {
            "up": (center_x - button_size // 2, y + 10),
            "down": (center_x - button_size // 2, y + panel_h - 10 - button_size),
            "left": (x + 12, center_y - button_size // 2),
            "right": (x + panel_w - 12 - button_size, center_y - button_size // 2),
        }
        for name, (button_x, button_y) in positions.items():
            self.display.setColor(self.BUTTON_FILL_COLOR if name in directions else self.PANEL_COLOR)
            self.display.fillRectangle(button_x, button_y, button_size, button_size)
            self.display.setColor(0x000000)
            self._draw_rect_outline(button_x, button_y, button_size, button_size)

        self.display.setColor(self.MUTED_TEXT_COLOR)
        self.display.drawText("U", center_x - 3, y + 13)
        self.display.drawText("D", center_x - 3, y + panel_h - 20)
        self.display.drawText("L", x + 16, center_y - 4)
        self.display.drawText("R", x + panel_w - 22, center_y - 4)

    def _draw_raw_readout(
        self,
        x: int,
        y: int,
        axes: Sequence[float],
        raw_axes: Sequence[float],
        axis_starts: Sequence[float],
        axis_mins: Sequence[float],
        axis_maxs: Sequence[float],
        axis_modes: Sequence[str],
        pressed_codes: Sequence[int],
        mapped_pressed_codes: Sequence[int],
        povs: Sequence[int],
    ) -> None:
        axes_text = " ".join(f"A{i}:{float(v):+.2f}" for i, v in enumerate(axes[: self.cfg.max_axes_shown]))
        cal_left = " ".join(
            f"A{i}{self._axis_mode_tag(axis_modes[i])}:{raw_axes[i]:.0f}@{axis_starts[i]:.0f}[{axis_mins[i]:.0f},{axis_maxs[i]:.0f}]"
            for i in range(min(2, len(raw_axes)))
        )
        cal_right = " ".join(
            f"A{i}{self._axis_mode_tag(axis_modes[i])}:{raw_axes[i]:.0f}@{axis_starts[i]:.0f}[{axis_mins[i]:.0f},{axis_maxs[i]:.0f}]"
            for i in range(2, min(4, len(raw_axes)))
        )
        raw_button_text = ", ".join(str(code + 1) for code in pressed_codes) if pressed_codes else "none"
        mapped_button_text = ", ".join(str(code + 1) for code in mapped_pressed_codes) if mapped_pressed_codes else "none"
        pov_text = ", ".join(str(value) for value in povs) if povs else "none"
        self.display.setColor(self.MUTED_TEXT_COLOR)
        self.display.drawText(f"Axes: {axes_text}", x, y)
        self.display.drawText(f"Range: {cal_left}", x, y + self.RAW_LINE_SPACING)
        self.display.drawText(f"Range: {cal_right}" if cal_right else "Range: sweep each axis once to learn full travel", x, y + self.RAW_LINE_SPACING * 2)
        self.display.drawText(f"Buttons raw: {raw_button_text}  driver: {mapped_button_text}  POV: {pov_text}", x, y + self.RAW_LINE_SPACING * 3)

    def update(
        self,
        axes: Sequence[float],
        buttons: Optional[Sequence[int]] = None,
        povs: Optional[Sequence[int]] = None,
        pressed_codes: Optional[Sequence[int]] = None,
        raw_axes: Optional[Sequence[float]] = None,
        axis_starts: Optional[Sequence[float]] = None,
        axis_mins: Optional[Sequence[float]] = None,
        axis_maxs: Optional[Sequence[float]] = None,
        axis_modes: Optional[Sequence[str]] = None,
        mapped_pressed_codes: Optional[Sequence[int]] = None,
        title: str = "Gamepad Visualizer",
        subtitle: str = "",
        connected: bool = False,
        active: bool = False,
        model: str = "",
        seconds_since_activity: float = 0.0,
        button_base: int = 0,
    ) -> None:
        buttons = buttons or []
        povs = povs or []
        pressed_codes = pressed_codes or []
        raw_axes = raw_axes or []
        axis_starts = axis_starts or []
        axis_mins = axis_mins or []
        axis_maxs = axis_maxs or []
        axis_modes = axis_modes or []
        mapped_pressed_codes = mapped_pressed_codes or []
        axis_labels = ["Y Rotation", "X Rotation", "Accelerator", "Brake"]
        xy_x = 14
        xy_y = 44
        xy_size = min(self.cfg.stick_size, max(64, self.H - 88))
        axis_x = xy_x + xy_size + 16
        axis_y = xy_y + 6
        buttons_x = axis_x + 140
        buttons_y = xy_y + 2
        pov_x = self.W - 100
        pov_y = xy_y + 2
        raw_y = max(self.H - (self.RAW_LINE_SPACING * 4) - 6, xy_y + xy_size + 8)

        self.display.setColor(self.BG_COLOR)
        self.display.fillRectangle(0, 0, self.W, self.H)

        self.display.setColor(self.TEXT_COLOR)
        self.display.drawText(title, 12, 8)
        self.display.setColor(self.MUTED_TEXT_COLOR)
        self.display.drawText(subtitle or "Windows-style test panel for your controller", 12, 24)

        self._draw_status(
            connected=connected,
            active=active,
            model=model,
            seconds_since_activity=seconds_since_activity,
            axis_count=len(axes),
            button_count=len(buttons),
            pov_count=len(povs),
        )

        self._draw_xy_test(xy_x, xy_y, self._axis_value(axes, 1), self._axis_value(axes, 0))

        for offset, axis_index in enumerate(range(2, min(len(axes), 6))):
            label = axis_labels[offset] if offset < len(axis_labels) else f"Axis {axis_index}"
            neutral = self._axis_neutral(axis_modes[axis_index]) if axis_index < len(axis_modes) else 0.0
            self._draw_axis_bar(axis_x, axis_y + offset * 18, 64, 12, label, self._axis_value(axes, axis_index), neutral)

        self._draw_buttons_panel(buttons_x, buttons_y, buttons, button_base)
        self._draw_pov_hat(pov_x, pov_y, povs[0] if povs else -1)
        self._draw_raw_readout(
            14,
            raw_y,
            axes,
            raw_axes,
            axis_starts,
            axis_mins,
            axis_maxs,
            axis_modes,
            pressed_codes,
            mapped_pressed_codes,
            povs,
        )


@dataclass
class PoseHudConfig:
    device_name: str = "hud"


class PoseHUD:
    """HUD for showing the active pose selection and key hints."""

    def __init__(self, robot, cfg: PoseHudConfig = PoseHudConfig()):
        self.cfg = cfg
        self.display = robot.getDevice(cfg.device_name)
        if not self.display:
            raise RuntimeError(f"HUD device '{cfg.device_name}' not found")
        self.W = self.display.getWidth()
        self.H = self.display.getHeight()

    def update(self, pose_name: str):
        self.display.setColor(0x000000)
        self.display.fillRectangle(0, 0, self.W, self.H)
        self.display.setColor(0xFFFFFF)
        self.display.drawText("Static Pose Test", 5, 5)
        self.display.drawText(f"Pose: {pose_name}", 5, 25)
        self.display.drawText("Keys: 1-9 select, N/P next/prev", 5, 45)
