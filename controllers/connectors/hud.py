# controllers/connectors/hud.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class HudConfig:
    device_name: str = "hud"
    max_axes_shown: int = 4
    max_buttons_shown: int = 10


class GamepadHUD:
    """Simple HUD for joystick axes/buttons using Webots Display device."""

    def __init__(self, robot, cfg: HudConfig = HudConfig()):
        self.cfg = cfg
        self.display = robot.getDevice(cfg.device_name)
        self.W = self.display.getWidth()
        self.H = self.display.getHeight()

    @staticmethod
    def _clamp01(x: float) -> float:
        return max(-1.0, min(1.0, float(x)))

    def _draw_axis_bar(self, y: int, val: float, label: str):
        val = self._clamp01(val)
        mid = 140
        scale = 120
        x1 = int(mid + val * scale)

        self.display.drawLine(mid - scale, y, mid + scale, y)  # baseline
        self.display.drawLine(mid, y, x1, y)                   # value
        self.display.drawText(label, 5, y - 12)

    def update(
        self,
        axes: List[float],
        buttons: Optional[List[int]] = None,
        title: str = "Gamepad HUD",
    ):
        self.display.setColor(0x000000)
        self.display.fillRectangle(0, 0, self.W, self.H)

        self.display.setColor(0xFFFFFF)
        self.display.drawText(title, 5, 5)

        labels = ["LX", "LY", "RX", "RY", "A4", "A5"]
        y0, dy = 45, 28
        n = min(self.cfg.max_axes_shown, len(axes))
        for i in range(n):
            v = float(axes[i])
            lab = labels[i] if i < len(labels) else f"A{i}"
            self._draw_axis_bar(y0 + dy * i, v, f"{lab}: {v:+.2f}")

        if buttons is not None:
            b = buttons[: self.cfg.max_buttons_shown]
            btn_text = " ".join(str(int(x)) for x in b)
            self.display.drawText(f"Buttons: {btn_text}", 5, self.H - 20)


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
