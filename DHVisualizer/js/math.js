// math.js
// DH parameter mathematics and forward kinematics

/**
 * Create a 4x4 DH transformation matrix (standard convention)
 * @param {number} a - link length
 * @param {number} alpha - link twist (radians)
 * @param {number} d - link offset
 * @param {number} theta - joint angle (radians)
 * @returns {Array<Array<number>>} 4x4 transformation matrix
 */
export function dhTransform(a, alpha, d, theta) {
    const ct = Math.cos(theta);
    const st = Math.sin(theta);
    const ca = Math.cos(alpha);
    const sa = Math.sin(alpha);
    
    return [
        [ct, -st * ca,  st * sa, a * ct],
        [st,  ct * ca, -ct * sa, a * st],
        [0,   sa,       ca,      d     ],
        [0,   0,        0,       1     ]
    ];
}

/**
 * Create a 4x4 DH transformation matrix (modified convention)
 * @param {number} a - link length
 * @param {number} alpha - link twist (radians)
 * @param {number} d - link offset
 * @param {number} theta - joint angle (radians)
 * @returns {Array<Array<number>>} 4x4 transformation matrix
 */
export function dhTransformModified(a, alpha, d, theta) {
    const ct = Math.cos(theta);
    const st = Math.sin(theta);
    const ca = Math.cos(alpha);
    const sa = Math.sin(alpha);
    
    return [
        [ct,    -st,     0,      a     ],
        [st*ca,  ct*ca, -sa,    -sa*d ],
        [st*sa,  ct*sa,  ca,     ca*d ],
        [0,      0,      0,      1    ]
    ];
}

/**
 * Multiply two 4x4 matrices
 * @param {Array<Array<number>>} a - first matrix
 * @param {Array<Array<number>>} b - second matrix
 * @returns {Array<Array<number>>} result matrix
 */
export function multiplyMatrices(a, b) {
    const result = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0]
    ];
    
    for (let i = 0; i < 4; i++) {
        for (let j = 0; j < 4; j++) {
            for (let k = 0; k < 4; k++) {
                result[i][j] += a[i][k] * b[k][j];
            }
        }
    }
    
    return result;
}

/**
 * Create an identity 4x4 matrix
 * @returns {Array<Array<number>>} identity matrix
 */
export function identityMatrix() {
    return [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ];
}

/**
 * Convert degrees to radians
 * @param {number} degrees
 * @returns {number} radians
 */
export function degToRad(degrees) {
    return degrees * Math.PI / 180;
}

/**
 * Convert radians to degrees
 * @param {number} radians
 * @returns {number} degrees
 */
export function radToDeg(radians) {
    return radians * 180 / Math.PI;
}

/**
 * Create a transformation matrix from position and rotation
 * @param {Object} transform - {x, y, z, rx, ry, rz} (rotations in radians)
 * @returns {Array<Array<number>>} 4x4 transformation matrix
 */
export function createTransform(transform) {
    const { x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0 } = transform;
    
    // Rotation matrices
    const cx = Math.cos(rx), sx = Math.sin(rx);
    const cy = Math.cos(ry), sy = Math.sin(ry);
    const cz = Math.cos(rz), sz = Math.sin(rz);
    
    // Combined rotation matrix (ZYX order)
    return [
        [cy*cz, -cy*sz, sy, x],
        [cx*sz + sx*sy*cz, cx*cz - sx*sy*sz, -sx*cy, y],
        [sx*sz - cx*sy*cz, sx*cz + cx*sy*sz, cx*cy, z],
        [0, 0, 0, 1]
    ];
}

/**
 * Forward kinematics for a single chain
 * @param {Object} chain - chain definition with joints array
 * @param {Array<number>} jointAngles - array of joint angles/offsets (radians)
 * @param {string} convention - "standard" or "modified"
 * @returns {Array<Array<Array<number>>>} array of 4x4 transformation matrices for each frame
 */
export function forwardKinematics(chain, jointAngles, convention = "standard") {
    const transforms = [];
    let currentTransform = identityMatrix();
    
    // Apply base transform if provided
    if (chain.baseTransform) {
        currentTransform = multiplyMatrices(currentTransform, chain.baseTransform);
    }
    
    // Add base frame
    transforms.push(JSON.parse(JSON.stringify(currentTransform)));
    
    // Compute each joint transform
    for (let i = 0; i < chain.joints.length; i++) {
        const joint = chain.joints[i];
        const angle = jointAngles[i] || 0;
        
        // Determine if this is a revolute (theta varies) or prismatic (d varies) joint
        // Default to revolute
        const theta = joint.theta + angle;
        const d = joint.d + (joint.isPrismatic ? angle : 0);
        
        // Create DH transform for this joint
        let dhMatrix;
        if (convention === "modified") {
            dhMatrix = dhTransformModified(joint.a, joint.alpha, d, theta);
        } else {
            dhMatrix = dhTransform(joint.a, joint.alpha, d, theta);
        }
        
        // Accumulate transform
        currentTransform = multiplyMatrices(currentTransform, dhMatrix);
        transforms.push(JSON.parse(JSON.stringify(currentTransform)));
    }
    
    return transforms;
}

/**
 * Extract position from a 4x4 transformation matrix
 * @param {Array<Array<number>>} matrix - 4x4 transformation matrix
 * @returns {Object} {x, y, z}
 */
export function getPosition(matrix) {
    return {
        x: matrix[0][3],
        y: matrix[1][3],
        z: matrix[2][3]
    };
}

/**
 * Extract rotation matrix from a 4x4 transformation matrix
 * @param {Array<Array<number>>} matrix - 4x4 transformation matrix
 * @returns {Array<Array<number>>} 3x3 rotation matrix
 */
export function getRotation(matrix) {
    return [
        [matrix[0][0], matrix[0][1], matrix[0][2]],
        [matrix[1][0], matrix[1][1], matrix[1][2]],
        [matrix[2][0], matrix[2][1], matrix[2][2]]
    ];
}

/**
 * Compute inverse kinematics for a chain (STUB for future implementation)
 * @param {Object} chain - chain definition
 * @param {Object} target - target position {x, y, z}
 * @param {Array<number>} initialGuess - initial joint angles
 * @returns {Array<number>|null} joint angles or null if no solution found
 * 
 * TODO: Implement IK solver
 * - For simple 2D/3D planar chains: analytical solution
 * - For general chains: numerical methods (Jacobian, gradient descent, etc.)
 * - Consider joint limits and singularities
 */
export function computeIK(chain, target, initialGuess) {
    // STUB: Return null to indicate no implementation yet
    console.warn('computeIK is not yet implemented. This is a stub for future IK solver.');
    console.log('Chain:', chain.id || chain.name);
    console.log('Target:', target);
    console.log('Initial guess:', initialGuess);
    
    // TODO: Implement your IK algorithm here
    // Possible approaches:
    // 1. Analytical IK for simple geometries (e.g., 3-DOF planar arm)
    // 2. Jacobian-based numerical IK (pseudo-inverse method)
    // 3. Cyclic Coordinate Descent (CCD)
    // 4. FABRIK (Forward And Backward Reaching Inverse Kinematics)
    
    return null;
}
