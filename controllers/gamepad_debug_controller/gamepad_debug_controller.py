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


INPUT_ACTIVITY_THRESHOLD = 0.08


def _has_visible_input(axes: list[float], buttons: list[int], threshold: float = INPUT_ACTIVITY_THRESHOLD) -> bool:
    return any(abs(float(axis)) > threshold for axis in axes) or any(int(button) == 1 for button in buttons)


def main() -> None:
    robot = Robot()
    timestep = int(robot.getBasicTimeStep())

    joystick = WebotsJoystick(timestep)
    try:
        hud = GamepadHUD(robot)
        print("[hud] overlay panel writes to Display 'hud'")
        print("[hud] if you do not see it: Robot > Display Devices > hud")
    except RuntimeError as exc:
        hud = None
        print(f"[hud] unavailable: {exc}")
    tick_count = 0
    print_every_ticks = 4
    show_raw_inputs = True
    last_activity_time = robot.getTime()
    print("[gamepad] visual monitor started")

    while robot.step(timestep) != -1:
        tick_count += 1
        current_time = robot.getTime()
        teleop, state = joystick.read()
        omega = teleop.wz
        input_active = _has_visible_input(state.axes, state.buttons)
        if input_active:
            last_activity_time = current_time

        connected = joystick.is_connected
        seconds_since_activity = max(0.0, current_time - last_activity_time)
        live = connected and seconds_since_activity < 0.25
        model_text = joystick.model or "no joystick"

        if tick_count % print_every_ticks == 0:
            status_text = "live" if live else "connected" if connected else "offline"
            print(
                f"[gamepad] status={status_text} model={model_text} "
                f"axes={len(state.axes)} buttons={len(state.buttons)} povs={len(state.povs)}"
            )
            print(
                f"[cmd_vel] vx={teleop.vx:+.3f} vy={teleop.vy:+.3f} omega={omega:+.3f} estop={int(teleop.estop)}"
            )
            if show_raw_inputs and connected:
                print(
                    f"[raw] raw_axes={state.raw_axes} normalized_axes={state.axes} "
                    f"starts={state.axis_starts} mins={state.axis_mins} maxs={state.axis_maxs} "
                    f"modes={state.axis_modes} raw_buttons={state.raw_buttons} driver_buttons={state.buttons} "
                    f"pressed_codes={state.pressed_codes} mapped_pressed_codes={state.mapped_pressed_codes} povs={state.povs}"
                )

        if hud:
            hud.update(
                axes=state.axes,
                buttons=state.buttons,
                povs=state.povs,
                pressed_codes=state.pressed_codes,
                raw_axes=state.raw_axes,
                axis_starts=state.axis_starts,
                axis_mins=state.axis_mins,
                axis_maxs=state.axis_maxs,
                axis_modes=state.axis_modes,
                mapped_pressed_codes=state.mapped_pressed_codes,
                title="Gamepad Visualizer",
                subtitle=(
                    f"vx={teleop.vx:+.2f}  vy={teleop.vy:+.2f}  "
                    f"omega={omega:+.2f}  estop={int(teleop.estop)}"
                ),
                connected=connected,
                active=live,
                model=model_text,
                seconds_since_activity=seconds_since_activity,
            )

    if not hud:
        print("[hud] add a Display device named 'hud' to see the visualizer")


if __name__ == "__main__":
    main()
