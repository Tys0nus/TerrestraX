# Quick Start Guide

## Running the Application

### The CORS Problem
The application uses ES6 modules which require an HTTP server. Opening `index.html` directly in your browser (`file://` protocol) will cause CORS errors and prevent the application from working.

### Solution: Start a Local Server

#### Windows (PowerShell)
```powershell
cd "e:\Vault\TheUnknownDimension\Terrestra Utilities\DHVisualizer"
python -m http.server 8000
```

Or double-click `start-server.bat`

#### Linux/Mac
```bash
cd "/path/to/DHVisualizer"
python3 -m http.server 8000
```

Or run `./start-server.sh`

### Access the Application
Once the server is running, open your browser and navigate to:
```
http://localhost:8000
```

## UI Design Philosophy

The interface now uses a **professional warm color palette**:

### Color Categories
- **Primary Actions** (brown `#8b6f47`): Main robot creation/management
- **Secondary Actions** (tan `#c19a6b`): File operations, edit mode
- **Success Actions** (sage `#7c9473`): Show all chains
- **Danger Actions** (terracotta `#c17b6f`): Hide all, delete
- **Neutral Actions** (warm gray `#9a9288`): Cancel buttons

### Design Principles
- **Consistent**: Button colors match their function across the entire UI
- **Professional**: No emojis, clean typography
- **Warm**: Soft tans, browns, and earth tones
- **Adaptive**: Automatically adjusts for light/dark system themes

## Creating Your First DH Table (Minimal Clicks)

1. **Start Fresh**: Click "New Robot"
   - Enter name (e.g., "MyArm")
   - Choose DH convention
   - Click "Create"

2. **Add a Chain**: Click "Add Chain"
   - Chain ID: `arm1`
   - Chain Name: `Robot Arm`
   - Number of Joints: `3`
   - Base Position: `0, 0, 0`
   - Click "Add Chain"

3. **Edit Parameters**: Click "Edit Mode"
   - Click on any DH parameter value in the table
   - Type new value
   - Press Enter or click outside

4. **Test Motion**: Use the joint sliders to see your robot move in real-time

5. **Save**: Click "Export" to save your robot as JSON

Total clicks: ~10-15 to create, configure, and test a new robot!

## Features

### Multi-Chain Support
- Visualize multiple kinematic chains simultaneously
- Independent DH parameter tables for each chain
- Per-chain visibility toggles

### Forward Kinematics
- Real-time FK computation using standard or modified DH conventions
- Visual feedback with coordinate frames at each joint
- End-effector position display

### Task Space Controls
- Set target end-effector positions (X, Y, Z)
- IK solver interface (stub implementation provided)
- Sync current EE position to target fields

### Import/Export
- Save robots as JSON files
- Load saved configurations
- Share robot definitions with others

## Troubleshooting

### Buttons Not Working
- Make sure you're accessing via `http://localhost:8000`, not `file://`
- Check browser console (F12) for errors
- Ensure Python is installed and server is running

### Joint Sliders Not Appearing
- Select a robot from the dropdown
- Ensure the robot has at least one chain defined
- Check that the chain is visible (toggle checkbox)

### 3D View Empty
- Camera might be too far - scroll to zoom in
- Try resetting view: refresh page
- Check that at least one chain is visible

## Next Steps

- Explore the 4 example robots (spider, 3-DOF arm, 6-DOF arm, hexapod)
- Implement your own IK solver in `js/math.js`
- Extend the UI for additional features (Jacobian visualization, collision detection, etc.)
- Customize the color scheme in `css/styles.css` CSS variables
