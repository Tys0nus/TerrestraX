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
    tick_count = 0
    print_every_ticks = 4
    show_raw_inputs = True
    print("[cmd_vel] streaming started (vx, vy, omega)")

    while robot.step(timestep) != -1:
        tick_count += 1
        teleop, state = joystick.read()
        omega = teleop.wz

        if tick_count % print_every_ticks == 0:
            print(
                f"[cmd_vel] vx={teleop.vx:+.3f} vy={teleop.vy:+.3f} omega={omega:+.3f} estop={int(teleop.estop)}"
            )
            if show_raw_inputs:
                print(f"[raw] axes={state.axes} buttons={state.buttons}")

        # Show LX,LY,RX,RY bars (use the axis_map indices)
        am = joystick.axis_map
        axes_view = []
        for idx in (am.lx, am.ly, am.rx, am.ry):
            axes_view.append(state.axes[idx] if 0 <= idx < len(state.axes) else 0.0)

        hud.update(
            axes_view,
            state.buttons,
            title=f"vx={teleop.vx:+.2f} vy={teleop.vy:+.2f} omega={omega:+.2f}",
        )


if __name__ == "__main__":
    main()
