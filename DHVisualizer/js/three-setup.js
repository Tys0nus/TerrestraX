// three-setup.js
// Three.js scene initialization and management

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export class ThreeSetup {
    constructor(container) {
        this.container = container;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.animationFrameId = null;
        this.transformControls = []; // Store active transform controls
        
        this.init();
    }

    init() {
        // Create scene
        this.scene = new THREE.Scene();
        
        // Auto-detect color scheme
        const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        this.scene.background = new THREE.Color(isDark ? 0x2a2623 : 0xfaf8f5);
        
        // Listen for color scheme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            this.scene.background = new THREE.Color(e.matches ? 0x2a2623 : 0xfaf8f5);
        });
        
        // Create camera
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(75, width / height, 0.001, 1000);
        this.camera.position.set(0.3, 0.3, 0.3); // Position for Z-up view
        this.camera.up.set(0, 0, 1); // Set Z-axis as up direction
        this.camera.lookAt(0, 0, 0);
        
        // Create renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);
        
        // Add orbit controls
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.screenSpacePanning = false;
        this.controls.minDistance = 0.1;
        this.controls.maxDistance = 10;
        this.controls.target.set(0, 0, 0); // Look at origin
        this.controls.update(); // Update controls to apply Z-up orientation
        
        // Add lights
        this.addLights();
        
        // Add grid and axes
        this.addHelpers();
        
        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());
        
        // Start animation loop
        this.animate();
    }

    addLights() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);
        
        // Directional light 1
        const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight1.position.set(5, 5, 5);
        this.scene.add(dirLight1);
        
        // Directional light 2
        const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
        dirLight2.position.set(-5, 3, -5);
        this.scene.add(dirLight2);
        
        // Point light at origin
        const pointLight = new THREE.PointLight(0xffffff, 0.5, 10);
        pointLight.position.set(0, 0, 0);
        this.scene.add(pointLight);
    }

    addHelpers() {
        // Grid helper (adaptive color) - rotate to XY plane for Z-up
        const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const gridSize = 1;
        const gridDivisions = 20;
        const grid = new THREE.GridHelper(
            gridSize, 
            gridDivisions, 
            isDark ? 0x4a453f : 0xe5e1dc,
            isDark ? 0x3a3430 : 0xf5f3f0
        );
        // Rotate grid 90 degrees to make it horizontal in Z-up coordinate system
        grid.rotation.x = Math.PI / 2;
        this.scene.add(grid);
        
        // World axes helper (larger, at origin)
        const worldAxes = new THREE.AxesHelper(0.1);
        this.scene.add(worldAxes);
    }

    onWindowResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        
        this.renderer.setSize(width, height);
    }

    animate() {
        this.animationFrameId = requestAnimationFrame(() => this.animate());
        
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    dispose() {
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
        }
        
        this.renderer.dispose();
        this.controls.dispose();
        
        if (this.container && this.renderer.domElement) {
            this.container.removeChild(this.renderer.domElement);
        }
    }

    getScene() {
        return this.scene;
    }

    getCamera() {
        return this.camera;
    }

    getRenderer() {
        return this.renderer;
    }
}
