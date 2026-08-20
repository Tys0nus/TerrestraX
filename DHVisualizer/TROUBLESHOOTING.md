# Troubleshooting Guide

## Common Issues and Solutions

### Issue: Nothing appears in the 3D viewport

**Symptoms**: The viewport shows only a dark background with grid.

**Solutions**:
1. **Select a robot**: Make sure you've selected a robot from the dropdown
2. **Activate chains**: Check at least one chain checkbox
3. **Check browser console**: Press F12 and look for errors
4. **Reload page**: Try Ctrl+F5 to force reload

**Verification**:
```javascript
// Open browser console (F12) and type:
window.dhVisualizer.getChainManager().getAllChains()
// Should return an object with chains
```

---

### Issue: Sliders don't affect the visualization

**Symptoms**: Moving sliders doesn't change the 3D model.

**Solutions**:
1. **Ensure chain is visible**: The chain checkbox must be checked
2. **Wait for initialization**: Give the page 2-3 seconds to fully load
3. **Check frame visibility**: Make sure the frame visibility checkbox is checked
4. **Clear cache**: Sometimes old JavaScript is cached (Ctrl+Shift+R)

**Verification**:
```javascript
// In console:
const chain = window.dhVisualizer.getChainManager().getChain('FL');
chain.setJointAngle(0, 0.5); // Should move the first joint
```

---

### Issue: "Cannot read property 'getChain' of undefined"

**Symptoms**: Error appears in console when clicking buttons.

**Solutions**:
1. **Wait for page load**: The application may still be initializing
2. **Check imports**: Open browser console and look for module loading errors
3. **Verify file paths**: Make sure all JS files are in the correct location
4. **Check CORS**: If running from `file://`, some browsers block module imports

**Best Practice**: Run from a local server:
```powershell
# Using Python
python -m http.server 8000

# Or using Node.js
npx http-server

# Then open: http://localhost:8000
```

---

### Issue: Three.js fails to load

**Symptoms**: Error message about THREE not being defined.

**Solutions**:
1. **Check internet connection**: Three.js is loaded from CDN
2. **Verify CDN link**: Ensure the script tags in index.html are correct
3. **Try local copy**: Download Three.js and update script src
4. **Check browser console**: Look for 404 errors on script loading

**Alternative**: Download Three.js locally:
```html
<!-- Replace CDN links with local files -->
<script src="lib/three.min.js"></script>
<script src="lib/OrbitControls.js"></script>
```

---

### Issue: Module import errors

**Symptoms**: "Failed to resolve module specifier" or similar.

**Solutions**:
1. **Use a web server**: Don't open HTML directly from file system
2. **Check file extensions**: All imports should use `.js` extension
3. **Verify paths**: All paths should be relative and correct
4. **Browser support**: Ensure browser supports ES6 modules

**Setup local server**:
```powershell
# PowerShell
cd "e:\Vault\TheUnknownDimension\Terrestra Utilities\DHVisualizer"
python -m http.server 8000
```

---

### Issue: Chains appear in wrong positions

**Symptoms**: Chains are not where expected in 3D space.

**Solutions**:
1. **Check base transforms**: Verify the baseTransform matrix in robots.js
2. **Verify DH parameters**: Ensure a, α, d, θ values are correct
3. **Check units**: All distances should be in meters, angles in radians
4. **Convention**: Verify using correct DH convention (standard vs modified)

**Debug helper**:
```javascript
// In console:
const chain = window.dhVisualizer.getChainManager().getChain('FL');
console.log('Base transform:', chain.baseTransform);
console.log('Current transforms:', chain.getAllTransforms());
```

---

### Issue: Performance is slow

**Symptoms**: Low frame rate, laggy interactions.

**Solutions**:
1. **Hide unused chains**: Uncheck chains you're not actively using
2. **Disable unnecessary frames**: Uncheck frame visibility for intermediate joints
3. **Reduce joint count**: Use simpler robot models for testing
4. **Close other browser tabs**: Free up GPU resources
5. **Update graphics drivers**: Ensure latest drivers installed

**Performance check**:
```javascript
// Check FPS (should be close to 60)
const stats = new Stats();
document.body.appendChild(stats.dom);
```

---

### Issue: IK button does nothing

**Symptoms**: "Solve IK" button shows alert but doesn't move robot.

**Expected Behavior**: This is normal! The IK solver is a stub.

**Solution**: Implement your own IK algorithm in `js/math.js`:
```javascript
export function computeIK(chain, target, initialGuess) {
    // Your IK implementation here
    // Return array of joint angles or null
    
    // Example stub:
    return null; // No solution (not implemented)
}
```

---

### Issue: Robot selector is empty

**Symptoms**: Dropdown shows only "Select a robot..."

**Solutions**:
1. **Check robots.js**: Ensure the file loaded correctly
2. **Verify export**: Make sure `export const robots = {...}` is present
3. **Browser console**: Look for syntax errors in robots.js
4. **File path**: Ensure robots.js is in the correct location

**Verification**:
```javascript
// In console:
import('./js/robots.js').then(m => console.log(m.robots));
// Should show all robot definitions
```

---

### Issue: Camera won't move

**Symptoms**: Can't rotate, pan, or zoom the 3D view.

**Solutions**:
1. **Check OrbitControls**: Ensure it loaded from CDN
2. **Click in viewport**: Make sure viewport has focus
3. **Browser compatibility**: Try a different browser
4. **Console errors**: Check for OrbitControls initialization errors

**Controls reminder**:
- **Rotate**: Left click + drag
- **Pan**: Right click + drag
- **Zoom**: Scroll wheel

---

### Issue: Colors look wrong or washed out

**Symptoms**: Visualization appears too bright/dark.

**Solutions**:
1. **Adjust lighting**: Modify light intensities in three-setup.js
2. **Material properties**: Check material settings for meshes
3. **Background color**: Change scene.background in three-setup.js
4. **Monitor calibration**: Check display settings

**Quick fix**:
```javascript
// In three-setup.js, adjust ambient light:
const ambientLight = new THREE.AmbientLight(0xffffff, 0.6); // Increase/decrease 0.6
```

---

### Issue: Console shows warnings

**Symptoms**: Yellow warnings in browser console.

**Common warnings and solutions**:

1. **"THREE.OrbitControls is deprecated"**
   - This is informational, can be ignored
   - Consider updating to newer Three.js version

2. **"computeIK is not yet implemented"**
   - This is expected, not an error
   - See section on implementing IK

3. **"DevTools failed to load source map"**
   - Cosmetic issue, doesn't affect functionality
   - Can be ignored or disabled in browser settings

---

## Browser-Specific Issues

### Chrome/Edge
- Usually works without issues
- Enable hardware acceleration for best performance
- Use Incognito mode to test without extensions

### Firefox
- May need to enable ES6 modules in about:config
- WebGL performance may vary
- Check `dom.moduleScripts.enabled` setting

### Safari
- Module imports may require HTTPS or local server
- WebGL support varies by version
- Try Safari Technology Preview for latest features

---

## Getting Help

### Debug Checklist
1. ✓ Browser console shows no errors
2. ✓ All JS files loaded successfully
3. ✓ Robot selected from dropdown
4. ✓ At least one chain checkbox checked
5. ✓ Three.js loaded from CDN
6. ✓ OrbitControls loaded successfully

### Information to Provide
When reporting issues, include:
- Browser name and version
- Operating system
- Console error messages (F12)
- Steps to reproduce
- Expected vs actual behavior

### Test File
Run `test.html` to verify the API:
```
Open test.html in browser
Click "Run All Tests"
Check for any failures
```

---

## Advanced Debugging

### Enable Verbose Logging
```javascript
// Add to main.js:
window.DEBUG = true;

// Then add logging in your functions:
if (window.DEBUG) console.log('Debug info:', data);
```

### Inspect Scene Objects
```javascript
// View all objects in scene:
console.log(window.dhVisualizer.getScene().children);

// Count objects:
console.log('Objects in scene:', 
    window.dhVisualizer.getScene().children.length);

// Find specific chain frames:
const frames = window.dhVisualizer.getScene().children
    .filter(obj => obj.name.includes('FL_frame'));
console.log('FL frames:', frames);
```

### Monitor Performance
```javascript
// Add FPS counter:
const stats = new Stats();
stats.showPanel(0); // 0: fps, 1: ms, 2: mb
document.body.appendChild(stats.dom);

// In animation loop:
stats.begin();
// ... rendering code ...
stats.end();
```

---

## Quick Fixes

### Reset Everything
```javascript
// In console:
window.location.reload(true); // Force reload
```

### Clear Cache
```
Chrome/Edge: Ctrl+Shift+Delete
Firefox: Ctrl+Shift+Delete
Safari: Cmd+Option+E
```

### Factory Reset
```javascript
// In console:
localStorage.clear();
sessionStorage.clear();
window.location.reload(true);
```

---

## Still Having Issues?

1. **Check README.md** for detailed documentation
2. **Review QUICKSTART.md** for basic usage
3. **Run test.html** to verify components
4. **Check code comments** for inline documentation
5. **Inspect browser console** for specific errors

Remember: The application requires a modern browser with ES6 module support and WebGL capabilities.
