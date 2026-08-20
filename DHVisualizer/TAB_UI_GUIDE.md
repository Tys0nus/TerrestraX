# Tab-Based UI Design

## Overview
The DH Visualizer now uses a **4-tab interface** that eliminates scrolling and organizes tools by task context.

## Tab Structure

### 🤖 Robot Tab
**Purpose**: Robot-level operations
- Select existing robot from dropdown
- Create new robot
- Export robot (JSON/URDF)
- Import robot from file

**When to use**: Starting a new project, switching robots, or saving/loading work

---

### 🔗 Chains Tab
**Purpose**: Kinematic chain management
- Show/Hide all chains at once
- Individual chain visibility toggles
- Chain selection for editing
- Add new chains to current robot

**When to use**: Managing multiple arms/legs, organizing complex robots

---

### 📊 Parameters Tab
**Purpose**: DH parameter editing
- DH parameter tables (one per chain)
- Joint type selection (revolute/prismatic/fixed)
- Virtual joint checkboxes
- Real-time parameter adjustment
- Theta sliders with angle display

**When to use**: Defining robot kinematics, tweaking joint parameters, setting virtual frames

**Auto-switches here when**: Robot is loaded from dropdown

---

### 🎯 Kinematics Tab
**Purpose**: Task-space control and manipulation
- End-effector position controls (X, Y, Z)
- Ragdoll mode toggle
  - Press `G` for translate mode
  - Press `R` for rotate mode
  - Press `Esc` to exit
- IK solving visualization

**When to use**: Interactive manipulation, testing workspace, inverse kinematics

---

## Workflow Examples

### Creating a New Robot
1. **Robot Tab** → Click "New Robot"
2. Enter name and convention
3. **Chains Tab** → Add chains
4. **Parameters Tab** → Auto-switches here, edit DH parameters
5. **Kinematics Tab** → Test end-effector control

### Loading a Preset
1. **Robot Tab** → Select from dropdown (e.g., "6-DOF Industrial Arm")
2. **Parameters Tab** → Auto-switches, view/edit parameters
3. **Chains Tab** → Toggle visibility if needed
4. **Kinematics Tab** → Test ragdoll mode

### Exporting to URDF
1. Ensure robot is complete in **Parameters Tab**
2. **Robot Tab** → Click "Export Robot"
3. Choose format: URDF, JSON, or Both
4. Download generated files for ROS/Gazebo

---

## Benefits
✅ **No scrolling** - All tools visible within tab context
✅ **Task-focused** - Related tools grouped together
✅ **Clean interface** - Reduces cognitive load
✅ **Fast navigation** - One click to any section
✅ **Smart defaults** - Auto-switches to relevant tabs
✅ **Visual feedback** - Active tab highlighted

## Technical Details
- Tab state managed by `tabs.js`
- Auto-switching on robot load (→ Parameters)
- CSS fade animation (0.2s) between tabs
- Keyboard shortcuts work across all tabs
- Tab badges available for notifications (future use)
