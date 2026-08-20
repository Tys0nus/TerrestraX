# Quick Start Guide - DH Visualizer

## Getting Started in 30 Seconds

### Step 1: Open the Application
- Double-click `index.html` or open it in any modern web browser
- The application loads with a dark-themed interface

### Step 2: Select a Robot
1. Look for the **Robot** dropdown at the top of the left panel
2. Click it and select "Spider Robot (Quadruped)"
3. The robot configuration loads (4 legs with 3 joints each)

### Step 3: Activate Chains
1. In the **Chains** section, you'll see checkboxes for each leg:
   - Front Left Leg
   - Front Right Leg
   - Rear Left Leg
   - Rear Right Leg
2. Click **"Show All Chains"** button to activate all 4 legs at once
3. Watch as all four legs appear in the 3D viewport!

### Step 4: Control Joint Angles
1. Scroll down to the **DH Parameters** section
2. Each active chain shows its joints with sliders
3. Drag any slider or type a value to move that joint
4. The 3D visualization updates in real-time

### Step 5: Navigate the 3D View
- **Rotate**: Left-click and drag
- **Pan**: Right-click and drag
- **Zoom**: Scroll wheel

### Step 6: Explore Task Space
1. Scroll to the **Task Space (IK)** section
2. See the current end-effector position (x, y, z) for each leg
3. Try the **"Sync from Joints"** button to update target position
4. The **"Solve IK"** button is ready for your custom IK implementation

## Try These Examples

### Example 1: Walking Pose
1. Select "Spider Robot (Quadruped)"
2. Show all chains
3. Set Front Left leg joints: [30°, -45°, 60°]
4. Set Front Right leg joints: [-30°, -45°, 60°]
5. Set Rear Left leg joints: [-30°, -45°, 60°]
6. Set Rear Right leg joints: [30°, -45°, 60°]

### Example 2: Single Robot Arm
1. Select "Simple 3-DOF Arm" from dropdown
2. Check the "Robot Arm" checkbox
3. Adjust the three joint angles to see different poses
4. Watch how the end-effector position changes

### Example 3: Hexapod Exploration
1. Select "Hexapod Robot"
2. Activate 2-3 legs at a time
3. Experiment with different leg configurations
4. Use "Show All Chains" for the full hexapod view

## Understanding the Interface

### Left Panel (Controls)
```
┌─────────────────────────┐
│ Robot Selector          │ ← Choose robot configuration
├─────────────────────────┤
│ Chains                  │ ← Toggle chains on/off
│  ☑ Show All / Hide All  │
├─────────────────────────┤
│ DH Parameters           │ ← Control each joint
│  Joint sliders & values │
├─────────────────────────┤
│ Task Space (IK)         │ ← End-effector & IK
│  Current position       │
│  Target inputs          │
└─────────────────────────┘
```

### Right Panel (3D Viewport)
- **Grid**: XY plane at Z=0
- **World Axes**: RGB = XYZ at origin
- **Chain Frames**: Smaller colored axes at each joint
- **Links**: Gray lines connecting joints
- **Spheres**: Yellow (base) or Cyan (joints)

## Tips & Tricks

### Performance
- Disable frame visibility checkboxes for joints you don't need to see
- Hide chains you're not currently working with
- The app handles 10+ chains smoothly

### Viewing
- Double-click the viewport to reset camera view
- Zoom in close to see joint details
- Zoom out to see the full robot structure

### Measurements
- All distances in meters (0.1 = 10cm)
- All angles in degrees in UI
- Internal calculations use radians

### Frame Visibility
- Uncheck the box next to a joint to hide its frame
- Useful for decluttering complex robots
- Links still visible even if frames are hidden

## Common Questions

**Q: Why don't I see anything in the 3D view?**
A: Make sure you've (1) selected a robot and (2) checked at least one chain checkbox.

**Q: How do I reset joint angles?**
A: Type 0 in the number input next to each slider.

**Q: Can I add my own robot?**
A: Yes! Edit `js/robots.js` and follow the examples. See README.md for details.

**Q: Does the IK solver work?**
A: It's a stub currently. You can implement your own IK algorithm in `js/math.js`.

**Q: Can I export the robot configuration?**
A: Not yet - this is planned for future versions. You can screenshot for now.

## Keyboard Shortcuts

Currently, the app uses mouse controls only. Keyboard shortcuts are planned for a future update.

## Next Steps

1. **Experiment**: Try all robot configurations
2. **Customize**: Add your own robot to `robots.js`
3. **Implement IK**: Write your own inverse kinematics solver
4. **Share**: This is a standalone HTML file - easy to share!

## Need Help?

- Check the `README.md` for full documentation
- Review the code comments in `js/` files
- Console (F12) shows useful debug information

---

**Happy Visualizing! 🤖**
