// robots.js
// Robot definitions with multiple kinematic chains

/**
 * Robot database with multi-chain support
 * Each robot can have multiple chains (e.g., quadruped with 4 legs)
 */
export const robots = {
    // Quadruped spider robot with 4 legs
    quadruped_spider: {
        name: "Spider Robot (Quadruped)",
        convention: "standard",
        description: "Quadruped robot with 4 legs, each with 3 DOF",
        chains: [
            {
                id: "FL",
                name: "Front Left Leg",
                baseTransform: [
                    [1, 0, 0, 0.06],   // X offset: 60mm forward
                    [0, 1, 0, 0.05],   // Y offset: 50mm left
                    [0, 0, 1, 0],      // Z offset: 0mm
                    [0, 0, 0, 1]
                ],
                joints: [
                    { a: 0.04, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.035, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.07, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false }
                ]
            },
            {
                id: "FR",
                name: "Front Right Leg",
                baseTransform: [
                    [1, 0, 0, 0.06],   // X offset: 60mm forward
                    [0, 1, 0, -0.05],  // Y offset: 50mm right
                    [0, 0, 1, 0],      // Z offset: 0mm
                    [0, 0, 0, 1]
                ],
                joints: [
                    { a: 0.04, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.035, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.07, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false }
                ]
            },
            {
                id: "RL",
                name: "Rear Left Leg",
                baseTransform: [
                    [1, 0, 0, -0.06],  // X offset: 60mm backward
                    [0, 1, 0, 0.05],   // Y offset: 50mm left
                    [0, 0, 1, 0],      // Z offset: 0mm
                    [0, 0, 0, 1]
                ],
                joints: [
                    { a: 0.04, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.035, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.07, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false }
                ]
            },
            {
                id: "RR",
                name: "Rear Right Leg",
                baseTransform: [
                    [1, 0, 0, -0.06],  // X offset: 60mm backward
                    [0, 1, 0, -0.05],  // Y offset: 50mm right
                    [0, 0, 1, 0],      // Z offset: 0mm
                    [0, 0, 0, 1]
                ],
                joints: [
                    { a: 0.04, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.035, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.07, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false }
                ]
            }
        ]
    },

    // Simple 3-DOF robot arm (single chain for comparison)
    simple_3dof: {
        name: "Simple 3-DOF Arm",
        convention: "standard",
        description: "Basic 3-DOF robot arm (single chain)",
        chains: [
            {
                id: "arm",
                name: "Robot Arm",
                baseTransform: [
                    [1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]
                ],
                joints: [
                    { a: 0, alpha: Math.PI/2, d: 0.1, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.15, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.15, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false }
                ]
            }
        ]
    },

    // 6-DOF industrial robot arm (single chain)
    industrial_6dof: {
        name: "6-DOF Industrial Arm",
        convention: "standard",
        description: "Industrial robot arm with 6 degrees of freedom",
        chains: [
            {
                id: "arm",
                name: "Robot Arm",
                baseTransform: [
                    [1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]
                ],
                joints: [
                    { a: 0, alpha: Math.PI/2, d: 0.15, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.2, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.2, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0, alpha: Math.PI/2, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0, alpha: -Math.PI/2, d: 0.15, theta: 0, visible: true, isPrismatic: false },
                    { a: 0, alpha: 0, d: 0.05, theta: 0, visible: true, isPrismatic: false }
                ]
            }
        ]
    },

    // Hexapod robot with 6 legs
    hexapod: {
        name: "Hexapod Robot",
        convention: "standard",
        description: "Hexapod robot with 6 legs, each with 3 DOF",
        chains: [
            {
                id: "L1",
                name: "Leg 1 (Front Right)",
                baseTransform: [
                    [Math.cos(Math.PI/6), -Math.sin(Math.PI/6), 0, 0.08],
                    [Math.sin(Math.PI/6), Math.cos(Math.PI/6), 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]
                ],
                joints: [
                    { a: 0.03, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.04, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.06, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false }
                ]
            },
            {
                id: "L2",
                name: "Leg 2 (Middle Right)",
                baseTransform: [
                    [0, -1, 0, 0],
                    [1, 0, 0, 0.08],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]
                ],
                joints: [
                    { a: 0.03, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.04, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.06, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false }
                ]
            },
            {
                id: "L3",
                name: "Leg 3 (Rear Right)",
                baseTransform: [
                    [Math.cos(-Math.PI/6), -Math.sin(-Math.PI/6), 0, -0.08],
                    [Math.sin(-Math.PI/6), Math.cos(-Math.PI/6), 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]
                ],
                joints: [
                    { a: 0.03, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.04, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.06, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false }
                ]
            },
            {
                id: "L4",
                name: "Leg 4 (Rear Left)",
                baseTransform: [
                    [Math.cos(-Math.PI/6), Math.sin(-Math.PI/6), 0, -0.08],
                    [-Math.sin(-Math.PI/6), Math.cos(-Math.PI/6), 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]
                ],
                joints: [
                    { a: 0.03, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.04, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.06, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false }
                ]
            },
            {
                id: "L5",
                name: "Leg 5 (Middle Left)",
                baseTransform: [
                    [0, 1, 0, 0],
                    [-1, 0, 0, -0.08],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]
                ],
                joints: [
                    { a: 0.03, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.04, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.06, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false }
                ]
            },
            {
                id: "L6",
                name: "Leg 6 (Front Left)",
                baseTransform: [
                    [Math.cos(Math.PI/6), Math.sin(Math.PI/6), 0, 0.08],
                    [-Math.sin(Math.PI/6), Math.cos(Math.PI/6), 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]
                ],
                joints: [
                    { a: 0.03, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.04, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false },
                    { a: 0.06, alpha: 0, d: 0, theta: 0, visible: true, isPrismatic: false }
                ]
            }
        ]
    }
};

/**
 * Get robot by ID
 * @param {string} robotId 
 * @returns {Object|null}
 */
export function getRobot(robotId) {
    return robots[robotId] || null;
}

/**
 * Get all robot IDs
 * @returns {Array<string>}
 */
export function getAllRobotIds() {
    return Object.keys(robots);
}

/**
 * Get all robots as array
 * @returns {Array<Object>}
 */
export function getAllRobots() {
    return Object.entries(robots).map(([id, robot]) => ({
        id,
        ...robot
    }));
}
