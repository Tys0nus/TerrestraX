# Creating Your Own DH Tables - Quick Guide

## 🚀 Super Fast Workflow (3 Clicks!)

### Option 1: Start From Scratch

1. **Click "➕ New Robot"** button
   - Enter robot name (e.g., "My Spider")
   - Choose DH convention (Standard/Modified)
   - Click "Create"

2. **Click "➕ Add Chain"** button
   - Enter chain ID (e.g., "leg1")
   - Enter chain name (e.g., "Front Left Leg")
   - Set number of joints (e.g., 3)
   - Set base position X, Y, Z (e.g., 0.06, 0.05, 0)
   - Click "Add Chain"

3. **Click "✏️ Edit Mode"** button
   - Now you can edit ALL DH parameters directly!
   - Change a, α, d values for each joint
   - Click "💾 Save Changes" when done

4. **Visualize!**
   - Check the chain checkbox
   - Move joint sliders to test
   - See immediate 3D feedback

### Option 2: Import Existing DH Tables

1. **Click "📂 Import"** button
2. Select your JSON file with DH parameters
3. Done! Robot loads with all chains

### Option 3: Start From Template

1. Select a built-in robot (e.g., "Spider Robot")
2. Click "💾 Export" to save as template
3. Edit the JSON file with your parameters
4. Click "📂 Import" to load your modified version

---

## 📝 Detailed Workflow

### Creating a New Robot

```
Step 1: Click "➕ New Robot"
├─ Robot Name: "My Quadruped"
├─ Convention: "Standard DH"
└─ Click "Create"

Step 2: Click "➕ Add Chain" (repeat for each leg)
├─ Chain ID: "FL" (short identifier)
├─ Chain Name: "Front Left Leg" (display name)
├─ Number of Joints: 3
├─ Base Position:
│  ├─ X: 0.06  (60mm forward)
│  ├─ Y: 0.05  (50mm left)
│  └─ Z: 0     (ground level)
└─ Click "Add Chain"

Step 3: Click "✏️ Edit Mode"
├─ Edit DH parameters in the tables:
│  ├─ Joint 1: a=0.04, α=0°, d=0
│  ├─ Joint 2: a=0.035, α=0°, d=0
│  └─ Joint 3: a=0.07, α=0°, d=0
└─ Click "💾 Save Changes"

Step 4: Visualize
├─ Check chain checkboxes
├─ Adjust joint sliders
└─ Test IK and jacobians
```

---

## 🎯 Edit Mode Features

When you click **"✏️ Edit Mode"**, you get:

### ✅ Editable DH Parameters
- Direct input fields for `a`, `α`, `d` values
- Changes highlighted in green
- Real-time validation

### ✅ Add/Remove Joints
- **"➕ Joint"** button: Add joints to any chain
- **"✖"** button: Delete individual joints
- Instantly see changes in 3D

### ✅ Delete Chains
- **"🗑️ Chain"** button: Remove entire chains
- Confirmation dialog to prevent accidents

### ✅ Save Changes
- Click **"💾 Save Changes"** to apply
- Immediate 3D update
- All sliders and controls refresh

---

## 💾 Import/Export Format

### Export JSON Structure
```json
{
  "id": "my_robot_123",
  "name": "My Robot",
  "convention": "standard",
  "description": "Custom robot",
  "chains": [
    {
      "id": "chain1",
      "name": "Chain 1",
      "baseTransform": [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
      ],
      "joints": [
        {
          "a": 0.1,
          "alpha": 0,
          "d": 0,
          "theta": 0,
          "visible": true,
          "isPrismatic": false
        }
      ]
    }
  ],
  "exportDate": "2025-12-04T..."
}
```

### Quick Edits in JSON
1. Export your robot
2. Open JSON in any text editor
3. Modify values (VSCode has great JSON support)
4. Import back into visualizer
5. Instant validation and 3D preview!

---

## 🔧 Common DH Table Patterns

### Planar 2-DOF Arm
```javascript
Chain: "arm"
├─ Joint 1: a=0.15, α=0°, d=0, θ=variable
└─ Joint 2: a=0.15, α=0°, d=0, θ=variable
```

### 3-DOF with Z-offset
```javascript
Chain: "arm"
├─ Joint 1: a=0, α=90°, d=0.1, θ=variable  (shoulder)
├─ Joint 2: a=0.15, α=0°, d=0, θ=variable  (elbow)
└─ Joint 3: a=0.15, α=0°, d=0, θ=variable  (wrist)
```

### Quadruped Leg Pattern
```javascript
Base: X=±0.06, Y=±0.05, Z=0 (4 corners)
Each Leg:
├─ Joint 1: a=0.04, α=0°, d=0  (coxa)
├─ Joint 2: a=0.035, α=0°, d=0 (femur)
└─ Joint 3: a=0.07, α=0°, d=0  (tibia)
```

---

## 🎨 Testing Your DH Table

### Visual Validation
1. ✅ Frames appear at correct positions
2. ✅ Links connect joints properly
3. ✅ End-effector reaches expected workspace
4. ✅ Joint angles produce expected motion

### Numerical Validation
1. Set all joints to 0°
2. Check end-effector position in Task Space
3. Compare with manual calculation
4. Adjust sliders, verify smooth motion

### IK Testing Workflow
1. Enable your chain
2. Move joints to a pose
3. Click "Sync from Joints" to get EE position
4. Note the position (x, y, z)
5. Change joint angles
6. Enter original position as target
7. Click "Solve IK" (implement your IK first!)

---

## 💡 Pro Tips

### Tip 1: Use Export for Backups
After creating each chain, export immediately. You can always import if you make a mistake.

### Tip 2: Clone and Modify
Start with a similar robot, export it, modify the JSON, import back.

### Tip 3: Symmetry
For symmetric robots (like quadrupeds):
1. Create one leg perfectly
2. Export
3. Copy the chain in JSON
4. Change ID and base transform
5. Import

### Tip 4: Incremental Testing
1. Start with 1 chain, 2 joints
2. Verify it works
3. Add more joints
4. Add more chains
5. Test after each addition

### Tip 5: Name Conventions
- Chain IDs: Short (FL, FR, arm1)
- Chain Names: Descriptive (Front Left Leg)
- Keep consistent naming across similar robots

---

## 🐛 Troubleshooting

### Chain doesn't appear?
- Check the chain checkbox is enabled
- Verify base transform isn't placing it too far away
- Check at least one joint has visible=true

### Edit mode not working?
- Make sure you created/selected a robot first
- Custom robots are fully editable
- Built-in robots need to be exported first, then re-imported

### Can't delete joints?
- You need at least 1 joint per chain
- Delete the chain if you want to start over

### Export button doesn't work?
- Select a robot first
- Check browser console (F12) for errors

---

## 📊 Example Workflow Times

| Task | Time | Clicks |
|------|------|--------|
| Create new robot | 10s | 3 |
| Add one chain | 15s | 2 |
| Edit 3 joints | 30s | 4 |
| Export for backup | 5s | 1 |
| Import existing | 5s | 2 |
| **Total for 4-leg robot** | **~2 min** | **~15** |

Compare to manual coding: 30+ minutes!

---

## 🎓 Learning Path

### Beginner
1. Load Spider Robot (built-in)
2. Move sliders, see how it works
3. Click Edit Mode, change one parameter
4. Export, examine JSON structure

### Intermediate
1. Create simple 2-DOF arm
2. Test forward kinematics
3. Export and modify in JSON editor
4. Import and verify

### Advanced
1. Create full quadruped from scratch
2. Implement IK solver in math.js
3. Test task-space control
4. Export library of custom robots

---

## 🚀 You're Ready!

**The fastest way to create DH tables:**
1. Click "➕ New Robot"
2. Click "➕ Add Chain" for each limb
3. Click "✏️ Edit Mode" to set parameters
4. Click "💾 Export" to save

**Then test your IK and Jacobians immediately in 3D!**

No more spreadsheets. No more guessing. Just instant visual feedback.

---

**Happy Robot Building! 🤖**
