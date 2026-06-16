# TerrestraX Project Summary

## Project Intent

TerrestraX is a spider-robot / quadruped robotics workspace built around Webots simulation, leg kinematics, iterative controller revisions, and a direct bridge toward bench hardware. The repository combines:

- robot geometry and configuration
- symbolic and numeric kinematics
- inverse kinematics and trajectory shaping
- gamepad teleoperation and debug HUDs
- simulation controllers for static and full-robot tests
- hardware output layers for Arduino serial and PCA9685 servo control
- planning artifacts for milestones, risks, validation, and tracker exports

The dominant engineering pattern in the repo is:

1. Define leg geometry and nominal standing targets.
2. Use forward kinematics and Jacobians to reason in foot space.
3. Convert desired foot motion into joint motion with bounded inverse kinematics.
4. Validate behavior in Webots first.
5. Reuse the same motion logic for hardware-facing servo backends.

This means the project is currently kinematics-driven first, with simulation and safe incremental bring-up taking priority over full dynamic gait optimization.

## Repository Structure

- `controllers/`
  Runtime logic for Webots, hardware tests, static-leg experiments, and connector layers.
- `core/`
  Mathematical foundation: types, forward kinematics, inverse kinematics, pose definitions, locomotion scaffolding, and trajectories.
- `robots/`
  Robot-specific leg chains, nominal pose generation, and hardware calibration defaults.
- `protos/`
  Webots robot definitions for the spider platform.
- `worlds/`
  Simulation environments for static and full-robot experiments.
- `planning/`
  Systems-engineering support: manifests, exports, trackers, risk templates, validation matrix, and workstream snapshots.
- `LTSpice experiments/`
  Electrical experimentation branch for supporting hardware design work.
- `architecture.md`
  Auto-generated module map used as the current architectural reference.

## Core Technical Approach

### 1. Simulation-first development

Webots is the main integration surface. Controllers use the Webots `Robot`, `Joystick`, and display/HUD APIs to validate motion logic before hardware deployment.

### 2. Leg-first modeling

The system models a leg as a 3-DOF chain with Denavit-Hartenberg parameters plus fixed alignment joints. The front-left leg is treated as the canonical chain, and the other legs are mirrored from it.

### 3. Foot-space control

Instead of commanding only joint angles by hand, the repo computes a desired foot position, then solves for joint motion using the Jacobian and a bounded resolved-rate inverse kinematics update.

### 4. Safe incremental behavior

The active controllers favor conservative behavior:

- start flat
- blend into a tucked / nominal body-height pose
- optionally move one leg in isolation
- hold the pose on command
- stop safely with an estop / hold behavior

This is a deliberate bring-up strategy that reduces debugging complexity while geometry, calibration, and controller assumptions are still being tuned.

### 5. Shared logic across simulation and hardware

The static leg controller is reused across both Webots and hardware-oriented execution. Only the output bridge changes:

- simulation writes motor positions directly
- hardware converts radians to calibrated servo degrees and sends them over serial or PCA9685 PWM

## Relevant Equations

The equations below are the important implemented ideas in the repo.

### 1. Denavit-Hartenberg link transform

Each link transform is built from the standard DH form:

$$
T_i =
\begin{bmatrix}
\cos\theta_i & -\sin\theta_i\cos\alpha_i & \sin\theta_i\sin\alpha_i & a_i\cos\theta_i \\
\sin\theta_i & \cos\theta_i\cos\alpha_i & -\cos\theta_i\sin\alpha_i & a_i\sin\theta_i \\
0 & \sin\alpha_i & \cos\alpha_i & d_i \\
0 & 0 & 0 & 1
\end{bmatrix}
$$

In code, revolute joints update $\theta_i$, prismatic joints update $d_i$, and fixed joints contribute alignment transforms only.

### 2. Chain forward kinematics

The full leg transform is the ordered product of link transforms:

$$
T(q) = \prod_{i=1}^{n} T_i(q_i)
$$

The foot position is extracted from the translation column of the final homogeneous transform:

$$
p(q) = T(q)_{0:3,3}
$$

### 3. Position Jacobian

The Jacobian used by inverse kinematics is the derivative of foot position with respect to joint coordinates:

$$
J(q) = \frac{\partial p(q)}{\partial q}
$$

This is derived symbolically and executed numerically.

### 4. Resolved-rate inverse kinematics

The leg inverse kinematics uses a pseudoinverse update:

$$
\Delta q = J(q)^{+} (p^{*} - p(q))
$$

where:

- $p^{*}$ is the desired foot position
- $p(q)$ is the current foot position
- $J(q)^{+}$ is the Moore-Penrose pseudoinverse

The bounded update step is:

$$
q_{k+1} = q_k + \alpha \, \mathrm{clip}(\Delta q, -\Delta q_{\max}, \Delta q_{\max})
$$

Convergence is checked through the Euclidean foot-position error:

$$
\|p^{*} - p(q)\| < \varepsilon
$$

### 5. Nominal standing pose from body height

The nominal pose is computed by keeping the zero-pose foot footprint in $x$ and $y$, while moving the body to a desired standing height $h$:

$$
p_{target} =
\begin{bmatrix}
p_x(q=0) \\
p_y(q=0) \\
-h
\end{bmatrix}
$$

For the other legs, the front-left solution is mirrored using sign changes per leg:

$$
p_{leg} = M_{leg} \, p_{FL}
$$

with mirror matrices equivalent to the sign patterns:

- FL: $(+x, +y, +z)$
- FR: $(+x, -y, +z)$
- RL: $(-x, +y, +z)$
- RR: $(-x, -y, +z)$

This is one of the most important design shortcuts in the project: solve one canonical leg cleanly, then reuse symmetry.

### 6. Time shaping for smooth motion

For bounded point-to-point motion, the repo uses the cubic smoothstep law:

$$
\tau = \frac{t}{T}
$$

$$
s(t) = 3\tau^2 - 2\tau^3
$$

$$
\dot{s}(t) = \frac{6\tau(1-\tau)}{T}
$$

$$
\ddot{s}(t) = \frac{6(1-2\tau)}{T^2}
$$

This gives zero start and end velocity for a smoother transition.

For repeating motion, the static controller uses phase wrapping:

$$
s_{static}(t) = \left(\frac{t}{T}\right) \bmod 1
$$

### 7. Static-leg sinusoidal path

The current static leg motion uses a simple periodic path around a nominal foot point $p_0$:

$$
x(s) = x_0 + A \sin(2\pi s)
$$

$$
y(s) = y_0
$$

$$
z(s) = z_0 + H \max(0, \sin(2\pi s))
$$

Interpretation:

- $A$ gives horizontal sweep amplitude
- $H$ gives upward lift height
- the `max(0, ...)` term keeps the leg from dipping below the base plane during the lower half of the cycle

This is a simple test trajectory, but it is very useful because it isolates IK quality, calibration quality, and solver stability.

### 8. Pose blending in the full spider controller

Whole-robot pose transitions are blended linearly in joint space:

$$
q_{blend}(\alpha) = (1-\alpha) q_{start} + \alpha q_{target}
$$

where $\alpha \in [0,1]$ progresses over a configured transition duration.

This is what lets the controller move from a flat pose to a tucked nominal pose without a step change in motor commands.

### 9. Servo calibration mapping for hardware

When driving real servos, radians are converted to calibrated servo angles:

$$
\theta_{deg} = \mathrm{clamp}(\theta_{offset} + d \cdot \theta_{rad} \cdot \frac{180}{\pi}, \theta_{min}, \theta_{max})
$$

where:

- $d \in \{-1, +1\}$ captures motor direction
- $\theta_{offset}$ is the servo center / mounting offset
- min and max bounds enforce safe motion limits

This is the final bridge between mathematical joint space and physical actuator space.

## Main Controllers and Their Roles

### `controllers/spider_controller/spider_controller.py`

This is the current full-robot Webots controller. Its main responsibilities are:

- dynamically discover four coxa, four femur, and four tibia motors
- support multiple motor-naming patterns used by different Webots worlds / proto expansions
- bind high-level gamepad actions (`tuck_body`, `move_front_left`, `hold_pose`, `estop`)
- blend from a flat pose to a nominal tucked pose
- optionally animate the front-left leg while the body remains tucked
- stream debug prints describing state, mode, and current joint targets

This controller shows the repo's current top-level control philosophy: safe transitions, explicit state logic, and operator visibility.

### `controllers/spider_static_controller/static_leg_common.py`

This is the reusable single-leg motion kernel. It:

- creates the canonical front-left leg chain
- seeds the controller with the nominal standing joint configuration
- computes a periodic target foot path
- runs a few bounded IK steps per control cycle
- returns the next joint vector

This file is the clearest expression of the repo's kinematics-first control stack.

### `controllers/spider_static_controller/spider_static_hardware_controller.py`

This file carries the static leg controller to real hardware by:

- selecting a backend (`arduino` or `pi-pca9685`)
- converting radians to calibrated servo degrees
- streaming motion at a configured loop rate
- supporting a safe per-joint calibration sweep mode

### `controllers/gamepad_debug_controller/gamepad_debug_controller.py`

This is the operator-interface debugging branch. It exists to verify:

- joystick connection state
- axis normalization and startup calibration
- button remapping
- POV decoding
- HUD presentation in Webots

That is important because control quality depends heavily on input quality.

## Tools and Technologies in Use

### Simulation and robot modeling

- Webots
- Webots controller API (`Robot`, `Joystick`, display / HUD integration)
- Webots `PROTO` robot definitions
- Webots simulation worlds for static and full-robot tests

### Math and control stack

- Python 3.10+
- NumPy for numeric vectors, Jacobian evaluation, and runtime control math
- SymPy for symbolic forward kinematics and Jacobian derivation
- dataclasses for clean parameter containers and controller state

### Input and debugging tools

- custom `WebotsJoystick` wrapper
- action-based `GamepadInput` abstraction
- runtime axis normalization, deadzone shaping, and button remapping
- HUD tools for gamepad and pose visualization

### Hardware and actuation tools

- Arduino serial bridge via `pyserial`
- direct PCA9685 PWM control through Adafruit CircuitPython libraries
- optional `adafruit-extended-bus` support for non-default I2C buses
- servo calibration layer with direction, offset, min, and max limits

### Development and verification tools

- Ruff
- pre-commit
- Jupyter notebooks for model and symbolic exploration
- ArchEx-generated `architecture.md`
- planning manifests, milestone exports, BOM templates, risk register, and validation matrix
- LTSpice experiment area for electronics-related exploration

### Lower-level / alternate implementation branch

- C source under `controllers/spider_static/` for low-level static-controller experimentation

## Branches of Thought

The repo shows several clear conceptual workstreams. These are not just separate files; they are separate engineering questions.

### 1. Geometric and kinematic branch

Question:
How should the leg be modeled so that pose and foot placement are mathematically tractable?

Evidence in repo:

- `core/kinematics.py`
- `core/inverse_kinematics.py`
- `robots/rconfig.py`
- symbolic helpers and notebooks

Outcome:
The project uses a canonical DH chain for the front-left leg and mirrors that solution across the robot.

### 2. Static single-leg validation branch

Question:
Can one leg follow a stable test trajectory before full gait logic is attempted?

Evidence in repo:

- `controllers/spider_static_controller/static_leg_common.py`
- static controller revisions (`rev01`, `mk02`, `mk03`, `mk04`)

Outcome:
The repo uses a sinusoidal foot path plus bounded IK as a repeatable test harness for solver and calibration quality.

### 3. Whole-body pose and transition branch

Question:
Can all four legs be moved into a stable nominal pose with safe transitions and minimal operator risk?

Evidence in repo:

- `controllers/spider_controller/spider_controller.py`
- nominal standing solution in `robots/rconfig.py`

Outcome:
The full-spider controller blends between pose maps, supports hold / estop behavior, and isolates optional motion to a single leg while the rest of the body remains stable.

### 4. Human input and visualization branch

Question:
Can operator input be made reliable enough to drive controller experiments?

Evidence in repo:

- `controllers/connectors/gamepad.py`
- `controllers/connectors/webots_joystick.py`
- `controllers/connectors/hud.py`
- `controllers/gamepad_debug_controller/gamepad_debug_controller.py`

Outcome:
The repo treats joystick normalization, axis calibration, button remapping, and HUD visibility as first-class engineering problems.

### 5. Simulation-to-hardware continuity branch

Question:
Can the same leg controller drive real actuators with only an output-layer swap?

Evidence in repo:

- `controllers/connectors/arduino_serial.py`
- `controllers/connectors/pca9685_i2c.py`
- `controllers/spider_static_controller/spider_static_hardware_controller.py`
- `robots/config_hw_static.py`

Outcome:
Yes, the repo is organized so that the motion generator stays the same while the actuator backend changes.

### 6. Revision and experimentation branch

Question:
How do design changes remain traceable while trying multiple controller variants?

Evidence in repo:

- `rev01` and `mk0x` naming patterns
- multiple world files
- notebooks
- prototype and static variants

Outcome:
The project keeps experimental history visible instead of collapsing everything into one controller too early.

### 7. Emerging locomotion branch

Question:
How will the project scale from static-leg tests to gait-level foot-target generation?

Evidence in repo:

- `core/locomotion/locomotion.py`
- leg phase offsets in `robots/rconfig.py`

Outcome:
The architectural direction is visible, but the most mature path today is still pose control plus static trajectory validation rather than a complete closed-loop gait engine.

### 8. Systems-engineering branch

Question:
How is the robotics effort being tracked beyond code?

Evidence in repo:

- `planning/tracker_manifest.json`
- `planning/exports/`
- `planning/templates/`

Outcome:
The repo is being treated as an engineering program, not only as a code drop. Validation, risks, milestones, and health are part of the workflow.

## Current State of the Project

The repository appears to be in a strong prototyping phase with a clear path from math -> simulation -> hardware:

- the kinematic and IK foundation is real and implemented
- nominal standing posture generation is automated
- the full-spider controller can discover motors dynamically and handle safe pose transitions
- the single-leg controller is reusable across simulation and hardware
- gamepad and HUD tooling exist specifically to reduce operator-side uncertainty
- full locomotion is hinted at architecturally, but static and staged control is the most mature branch

In practical terms, the project is already beyond a toy simulation. It has become a robotics development platform with parallel tracks in control, hardware, operator tooling, and planning.

## Concise One-Sentence Summary

TerrestraX is a Webots-centered spider-robot platform that uses DH-based kinematics, Jacobian inverse kinematics, smooth trajectory shaping, gamepad-driven controller experiments, and interchangeable servo backends to move from simulation-grade leg control toward real hardware deployment.