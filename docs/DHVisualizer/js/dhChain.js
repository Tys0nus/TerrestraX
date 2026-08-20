// dhChain.js
// Management of individual kinematic chains and their 3D visualization

import * as THREE from 'three';
import { TransformControls } from 'three/addons/controls/TransformControls.js';
import { forwardKinematics, getPosition, degToRad } from './math.js';

/**
 * DHChain class manages a single kinematic chain
 * Handles FK computation, 3D frame visualization, and state management
 */
export class DHChain {
    constructor(chainDefinition, scene, convention = "standard") {
        this.id = chainDefinition.id;
        this.name = chainDefinition.name;
        this.baseTransform = chainDefinition.baseTransform;
        this.joints = JSON.parse(JSON.stringify(chainDefinition.joints)); // Deep copy
        this.scene = scene;
        this.convention = convention;
        
        // Current joint angles (in radians)
        this.jointAngles = new Array(this.joints.length).fill(0);
        
        // 3D objects for each frame
        this.frameObjects = {}; // { "frame_0": {axes, sphere, group}, ... }
        
        // Transformation matrices for each frame
        this.transforms = [];
        
        // Visibility state
        this.isVisible = false;
        
        // Interactive end-effector manipulation
        this.transformControl = null;
        this.ragdollMode = false;
        this.ikCallback = null; // Callback function for IK solving
    }

    /**
     * Update joint angle at specific index
     * @param {number} index - joint index
     * @param {number} angle - angle in radians
     */
    setJointAngle(index, angle) {
        if (index >= 0 && index < this.jointAngles.length) {
            this.jointAngles[index] = angle;
            this.updateFK();
        }
    }

    /**
     * Set all joint angles at once
     * @param {Array<number>} angles - array of angles in radians
     */
    setAllJointAngles(angles) {
        this.jointAngles = [...angles];
        this.updateFK();
    }

    /**
     * Get current joint angles
     * @returns {Array<number>}
     */
    getJointAngles() {
        return [...this.jointAngles];
    }

    /**
     * Update forward kinematics
     */
    updateFK() {
        const chainDef = {
            baseTransform: this.baseTransform,
            joints: this.joints
        };
        
        this.transforms = forwardKinematics(chainDef, this.jointAngles, this.convention);
        
        if (this.isVisible) {
            this.updateVisualization();
        }
        
        // Update transform control position if ragdoll mode is active
        if (this.ragdollMode) {
            this.updateTransformControlPosition();
        }
    }

    /**
     * Show the chain in the 3D scene
     */
    show() {
        this.isVisible = true;
        this.updateFK();
        this.updateVisualization();
    }

    /**
     * Hide the chain from the 3D scene
     */
    hide() {
        this.isVisible = false;
        this.removeAllFrames();
    }

    /**
     * Toggle frame visibility at specific index
     * @param {number} index - frame index
     * @param {boolean} visible - visibility state
     */
    setFrameVisible(index, visible) {
        if (index >= 0 && index < this.joints.length) {
            this.joints[index].visible = visible;
            this.updateVisualization();
        }
    }

    /**
     * Update 3D visualization of all frames
     */
    updateVisualization() {
        if (!this.isVisible) {
            return;
        }

        // Update each frame (skip base frame at index 0 for joint visibility)
        for (let i = 0; i < this.transforms.length; i++) {
            const frameId = `frame_${i}`;
            const transform = this.transforms[i];
            
            // Determine if this frame should be visible
            // Base frame (i=0) is always visible
            // Joint frames (i>0) use the joint's visibility setting
            const shouldBeVisible = i === 0 || this.joints[i - 1].visible;
            
            if (shouldBeVisible) {
                this.createOrUpdateFrame(frameId, transform, i);
            } else {
                this.removeFrame(frameId);
            }
        }
        
        // Update links separately
        this.updateLinks();
    }

    /**
     * Create or update a single frame visualization
     * @param {string} frameId - unique frame identifier
     * @param {Array<Array<number>>} transform - 4x4 transformation matrix
     * @param {number} index - frame index
     */
    createOrUpdateFrame(frameId, transform, index) {
        const fullId = `${this.id}_${frameId}`;
        
        if (!this.frameObjects[frameId]) {
            // Create new frame
            const group = new THREE.Group();
            group.name = fullId;
            
            // Create axes helper
            const axesSize = index === 0 ? 0.03 : 0.02; // Base frame slightly larger
            const axes = new THREE.AxesHelper(axesSize);
            group.add(axes);
            
            // Create origin sphere
            const sphereRadius = index === 0 ? 0.005 : 0.003;
            const sphereGeometry = new THREE.SphereGeometry(sphereRadius, 8, 8);
            const sphereMaterial = new THREE.MeshBasicMaterial({ 
                color: index === 0 ? 0xffff00 : 0x00ffff 
            });
            const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
            group.add(sphere);
            
            this.scene.add(group);
            this.frameObjects[frameId] = { group, axes, sphere };
        }
        
        // Update transform
        const group = this.frameObjects[frameId].group;
        this.applyMatrixToGroup(group, transform);
    }

    /**
     * Apply 4x4 matrix to Three.js group
     * @param {THREE.Group} group 
     * @param {Array<Array<number>>} matrix 
     */
    applyMatrixToGroup(group, matrix) {
        // Convert DH matrix (4x4 array) to Three.js Matrix4
        // Everything stays in Z-up; camera orientation handles the view
        const m = new THREE.Matrix4();
        m.set(
            matrix[0][0], matrix[0][1], matrix[0][2], matrix[0][3],
            matrix[1][0], matrix[1][1], matrix[1][2], matrix[1][3],
            matrix[2][0], matrix[2][1], matrix[2][2], matrix[2][3],
            matrix[3][0], matrix[3][1], matrix[3][2], matrix[3][3]
        );
        
        group.position.setFromMatrixPosition(m);
        group.rotation.setFromRotationMatrix(m);
        group.scale.setFromMatrixScale(m);
    }
    
    /**
     * Update link visualizations between joints
     */
    updateLinks() {
        // Remove old links
        if (!this.linkObjects) {
            this.linkObjects = [];
        }
        
        this.linkObjects.forEach(link => {
            this.scene.remove(link);
        });
        this.linkObjects = [];
        
        // Create new links between consecutive frames
        for (let i = 1; i < this.transforms.length; i++) {
            const prevPos = getPosition(this.transforms[i - 1]);
            const currPos = getPosition(this.transforms[i]);
            
            const points = [
                new THREE.Vector3(prevPos.x, prevPos.y, prevPos.z),
                new THREE.Vector3(currPos.x, currPos.y, currPos.z)
            ];
            
            const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
            const lineMaterial = new THREE.LineBasicMaterial({ 
                color: 0xa0825a,
                linewidth: 2
            });
            const line = new THREE.Line(lineGeometry, lineMaterial);
            
            this.scene.add(line);
            this.linkObjects.push(line);
        }
    }

    /**
     * Remove a specific frame from the scene
     * @param {string} frameId 
     */
    removeFrame(frameId) {
        if (this.frameObjects[frameId]) {
            this.scene.remove(this.frameObjects[frameId].group);
            delete this.frameObjects[frameId];
        }
    }

    /**
     * Clear all visualization objects (frames and links)
     */
    clearVisualization() {
        // Remove all frame objects
        Object.keys(this.frameObjects).forEach(frameId => {
            this.scene.remove(this.frameObjects[frameId].group);
        });
        this.frameObjects = {};
        
        // Remove all link objects
        this.linkObjects.forEach(link => {
            this.scene.remove(link);
        });
        this.linkObjects = [];
    }

    /**
     * Remove all frames from the scene
     */
    removeAllFrames() {
        Object.keys(this.frameObjects).forEach(frameId => {
            this.removeFrame(frameId);
        });
        
        // Remove all links
        if (this.linkObjects) {
            this.linkObjects.forEach(link => {
                this.scene.remove(link);
            });
            this.linkObjects = [];
        }
    }

    /**
     * Get end-effector position (last frame)
     * @returns {Object} {x, y, z}
     */
    getEndEffectorPosition() {
        if (this.transforms.length > 0) {
            return getPosition(this.transforms[this.transforms.length - 1]);
        }
        return { x: 0, y: 0, z: 0 };
    }

    /**
     * Get transform at specific frame index
     * @param {number} index 
     * @returns {Array<Array<number>>|null}
     */
    getTransform(index) {
        return this.transforms[index] || null;
    }

    /**
     * Get all transforms
     * @returns {Array<Array<Array<number>>>}
     */
    getAllTransforms() {
        return this.transforms;
    }
    
    /**
     * Enable ragdoll mode - interactive end-effector manipulation
     * @param {Function} ikCallback - Callback function(targetPos, targetRot)
     */
    enableRagdollMode(ikCallback) {
        if (this.ragdollMode) return;
        
        this.ragdollMode = true;
        this.ikCallback = ikCallback;
        
        // Get end-effector position and create transform control
        const eePos = this.getEndEffectorPosition();
        
        // Create a target object for the transform control
        const geometry = new THREE.SphereGeometry(0.015, 16, 16);
        const material = new THREE.MeshBasicMaterial({ 
            color: 0xa0825a,
            transparent: true,
            opacity: 0.7
        });
        this.transformTarget = new THREE.Mesh(geometry, material);
        this.transformTarget.position.set(eePos.x, eePos.y, eePos.z);
        this.scene.add(this.transformTarget);
        
        // Create transform control
        this.transformControl = new TransformControls(
            window.threeSetup.camera,
            window.threeSetup.renderer.domElement
        );
        this.transformControl.attach(this.transformTarget);
        this.transformControl.setMode('translate'); // Start with translate mode
        this.transformControl.setSize(0.5);
        this.scene.add(this.transformControl);
        
        // Listen for transform changes
        this.transformControl.addEventListener('dragging-changed', (event) => {
            // Disable orbit controls during drag
            window.threeSetup.controls.enabled = !event.value;
        });
        
        this.transformControl.addEventListener('change', () => {
            if (this.ikCallback) {
                const pos = this.transformTarget.position;
                const rot = this.transformTarget.quaternion;
                this.ikCallback({ x: pos.x, y: pos.y, z: pos.z }, rot);
            }
        });
        
        // Add keyboard shortcuts
        this.keyboardHandler = (event) => {
            if (!this.ragdollMode) return;
            
            switch (event.key.toLowerCase()) {
                case 'g':
                    this.transformControl.setMode('translate');
                    break;
                case 'r':
                    this.transformControl.setMode('rotate');
                    break;
                case 'escape':
                    const checkbox = document.getElementById(`ragdoll-${this.id}`);
                    if (checkbox) {
                        checkbox.checked = false;
                        checkbox.dispatchEvent(new Event('change'));
                    }
                    break;
            }
        };
        
        window.addEventListener('keydown', this.keyboardHandler);
    }
    
    /**
     * Disable ragdoll mode
     */
    disableRagdollMode() {
        if (!this.ragdollMode) return;
        
        this.ragdollMode = false;
        this.ikCallback = null;
        
        // Remove transform control
        if (this.transformControl) {
            this.transformControl.detach();
            this.scene.remove(this.transformControl);
            this.transformControl.dispose();
            this.transformControl = null;
        }
        
        // Remove target object
        if (this.transformTarget) {
            this.scene.remove(this.transformTarget);
            this.transformTarget = null;
        }
        
        // Remove keyboard handler
        if (this.keyboardHandler) {
            window.removeEventListener('keydown', this.keyboardHandler);
            this.keyboardHandler = null;
        }
        
        // Re-enable orbit controls
        if (window.threeSetup && window.threeSetup.controls) {
            window.threeSetup.controls.enabled = true;
        }
    }
    
    /**
     * Update transform control position to match current end-effector
     */
    updateTransformControlPosition() {
        if (this.transformControl && this.transformTarget) {
            const eePos = this.getEndEffectorPosition();
            this.transformTarget.position.set(eePos.x, eePos.y, eePos.z);
        }
    }

    /**
     * Dispose of all resources
     */
    dispose() {
        this.removeAllFrames();
    }
}

/**
 * ChainManager manages multiple DHChain instances
 */
export class ChainManager {
    constructor(scene, convention = "standard") {
        this.scene = scene;
        this.convention = convention;
        this.chains = {}; // { chainId: DHChain }
    }

    /**
     * Add a new chain
     * @param {Object} chainDefinition 
     * @returns {DHChain}
     */
    addChain(chainDefinition) {
        const chain = new DHChain(chainDefinition, this.scene, this.convention);
        this.chains[chain.id] = chain;
        return chain;
    }

    /**
     * Get chain by ID
     * @param {string} chainId 
     * @returns {DHChain|null}
     */
    getChain(chainId) {
        return this.chains[chainId] || null;
    }

    /**
     * Get all chains
     * @returns {Object}
     */
    getAllChains() {
        return this.chains;
    }

    /**
     * Remove chain by ID
     * @param {string} chainId 
     */
    removeChain(chainId) {
        const chain = this.chains[chainId];
        if (chain) {
            chain.dispose();
            delete this.chains[chainId];
        }
    }

    /**
     * Remove all chains
     */
    removeAllChains() {
        Object.keys(this.chains).forEach(chainId => {
            this.removeChain(chainId);
        });
    }

    /**
     * Show all chains
     */
    showAllChains() {
        Object.values(this.chains).forEach(chain => {
            chain.show();
        });
    }

    /**
     * Hide all chains
     */
    hideAllChains() {
        Object.values(this.chains).forEach(chain => {
            chain.hide();
        });
    }

    /**
     * Update convention for all chains
     * @param {string} convention 
     */
    setConvention(convention) {
        this.convention = convention;
        Object.values(this.chains).forEach(chain => {
            chain.convention = convention;
            chain.updateFK();
        });
    }
}
