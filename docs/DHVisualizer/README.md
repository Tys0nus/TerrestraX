# DH Parameter Visualizer - Multi-Chain

A powerful web-based tool for visualizing multiple kinematic chains using Denavit-Hartenberg (DH) parameters. Built with HTML, JavaScript, and Three.js.

## Features

### ✅ Multi-Chain Support
- Visualize multiple kinematic chains simultaneously
- Each chain has its own DH parameter table
- Independent base transforms for each chain
- Perfect for quadrupeds, hexapods, and multi-arm robots

### ✅ Real-Time 3D Visualization
- Interactive 3D scene powered by Three.js
- Orbit controls for camera manipulation
- Color-coded coordinate frames
- Visual links between frames
- Grid and axis helpers

### ✅ Dynamic UI Controls
- **Robot Selection**: Choose from predefined robot configurations
- **Chain Toggles**: Show/hide individual chains
- **Joint Controls**: Real-time sliders for each joint angle
- **Frame Visibility**: Toggle visibility of individual frames
- **Task Space Panel**: View end-effector position and IK controls

### ✅ Included Robot Examples
1. **Spider Robot (Quadruped)**: 4 legs with 3 DOF each
2. **Simple 3-DOF Arm**: Basic robot arm
3. **6-DOF Industrial Arm**: Standard industrial manipulator
4. **Hexapod Robot**: 6 legs with 3 DOF each

### ✅ Forward Kinematics
- Standard DH convention support
- Modified DH convention support
- Real-time transformation matrix computation
- End-effector position tracking

### ✅ Inverse Kinematics (Stub)
- IK interface ready for custom implementation
- Task-space controls with target position inputs
- "Solve IK" button (stub for future solver)
- "Sync from Joints" button to update target from current pose

## File Structure

```
DHVisualizer/
├── index.html              # Main HTML entry point
├── css/
│   └── styles.css         # Application styling
├── js/
│   ├── main.js            # Application coordinator
│   ├── three-setup.js     # Three.js scene initialization
│   ├── math.js            # DH mathematics and FK/IK
│   ├── robots.js          # Robot definitions
│   ├── dhChain.js         # Chain management and visualization
│   └── ui-controls.js     # UI generation and event handling
└── README.md              # This file
```

## Usage

### Opening the Application

1. Simply open `index.html` in a modern web browser
2. No build process or server required
3. All dependencies loaded via CDN

### Using the Interface

1. **Select a Robot**: Choose from the dropdown menu
2. **Activate Chains**: Check boxes to show/hide chains
3. **Adjust Joints**: Use sliders to change joint angles
4. **Toggle Frames**: Show/hide individual coordinate frames
5. **View End-Effector**: Check task space panel for EE position
6. **Navigate 3D**: Left-click drag to rotate, right-click to pan, scroll to zoom

### Quick Start Example

```javascript
// Access the visualizer instance
const viz = window.dhVisualizer;

// Get a specific chain
const chain = viz.getChainManager().getChain('FL');

// Set joint angles programmatically (radians)
chain.setAllJointAngles([0.5, -0.3, 0.8]);

// Get end-effector position
const eePos = chain.getEndEffectorPosition();
console.log('EE Position:', eePos);
```

## Adding Custom Robots

Edit `js/robots.js` to add new robot configurations:

```javascript
export const robots = {
    my_custom_robot: {
        name: "My Custom Robot",
        convention: "standard",
        description: "Description here",
        chains: [
            {
                id: "chain1",
                name: "Chain 1",
                baseTransform: [
                    [1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]
                ],
                joints: [
                    { a: 0.1, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    // Add more joints...
                ]
            }
            // Add more chains...
        ]
    }
};
```

## DH Parameter Convention

### Standard DH Convention (Default)
```
T = Rot(Z, θ) * Trans(Z, d) * Trans(X, a) * Rot(X, α)
```

Parameters:
- `a`: Link length (distance along X)
- `α` (alpha): Link twist (rotation about X)
- `d`: Link offset (distance along Z)
- `θ` (theta): Joint angle (rotation about Z)

### Modified DH Convention
```
T = Trans(X, a) * Rot(X, α) * Rot(Z, θ) * Trans(Z, d)
```

## Implementing Custom IK

The `computeIK()` function in `js/math.js` is provided as a stub. To implement your own IK solver:

```javascript
export function computeIK(chain, target, initialGuess) {
    // TODO: Implement your IK algorithm
    
    // Example approaches:
    // 1. Analytical IK for specific geometries
    // 2. Jacobian-based numerical IK
    // 3. Cyclic Coordinate Descent (CCD)
    // 4. FABRIK algorithm
    
    // Return array of joint angles or null
    return jointAngles;
}
```

## API Reference

### DHChain Class

```javascript
// Set joint angle (radians)
chain.setJointAngle(index, angle);

// Set all joint angles
chain.setAllJointAngles([θ1, θ2, θ3]);

// Get joint angles
const angles = chain.getJointAngles();

// Show/hide chain
chain.show();
chain.hide();

// Get end-effector position
const pos = chain.getEndEffectorPosition(); // {x, y, z}

// Get transform at frame
const T = chain.getTransform(index);
```

### ChainManager Class

```javascript
// Add chain
const chain = chainManager.addChain(chainDefinition);

// Get chain
const chain = chainManager.getChain(chainId);

// Show/hide all chains
chainManager.showAllChains();
chainManager.hideAllChains();

// Remove chains
chainManager.removeChain(chainId);
chainManager.removeAllChains();
```

## Technical Details

### Dependencies
- **Three.js r160**: 3D rendering and scene management
- **OrbitControls**: Camera interaction

### Browser Compatibility
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

### Performance
- Optimized for up to 10 chains simultaneously
- Each chain can have up to 10 joints
- 60 FPS rendering on modern hardware

## Troubleshooting

### Chains Not Appearing
- Ensure the chain checkbox is checked
- Verify base transform is not placing chain outside view
- Check browser console for errors

### Sliders Not Working
- Make sure chain is activated first
- Check that robot is selected in dropdown
- Verify joint angles are within valid range

### IK Button Does Nothing
- This is expected - IK is a stub for custom implementation
- See "Implementing Custom IK" section above

## Future Enhancements

- [ ] Implement default IK solvers (analytical, numerical)
- [ ] Add joint limit constraints
- [ ] Export/import robot configurations (JSON)
- [ ] Animation timeline and keyframes
- [ ] Collision detection between chains
- [ ] URDF file import
- [ ] Screenshot and video export
- [ ] Touch controls for mobile devices

## License

This project is open source and available for educational and commercial use.

## Credits

Created for robotics education and visualization. Built with modern web technologies for maximum accessibility and ease of use.

---

**Version**: 1.0.0  
**Last Updated**: December 4, 2025
