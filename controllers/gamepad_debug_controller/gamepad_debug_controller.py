"""Debug controller to visualize gamepad input on the Webots HUD."""
from __future__ import annotations

import os
import sys
from controller import Robot

# Add the 'controllers' folder to sys.path so we can import connectors/*
CONTROLLERS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if CONTROLLERS_DIR not in sys.path:
    sys.path.append(CONTROLLERS_DIR)

from connectors.hud import GamepadHUD  # noqa: E402
from connectors.webots_joystick import WebotsJoystick  # noqa: E402


def main() -> None:
    robot = Robot()
    timestep = int(robot.getBasicTimeStep())

    joystick = WebotsJoystick(timestep)
    hud = GamepadHUD(robot)

    while robot.step(timestep) != -1:
        teleop, state = joystick.read()

        # Show LX,LY,RX,RY bars (use the axis_map indices)
        am = joystick.axis_map
        axes_view = []
        for idx in (am.lx, am.ly, am.rx, am.ry):
            axes_view.append(state.axes[idx] if 0 <= idx < len(state.axes) else 0.0)

        hud.update(
            axes_view,
            state.buttons,
            title=f"vx={teleop.vx:+.2f} vy={teleop.vy:+.2f} wz={teleop.wz:+.2f}",
        )


if __name__ == "__main__":
    main()
