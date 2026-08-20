// main.js
// Application entry point - coordinates all modules

import { ThreeSetup } from './three-setup.js';
import { ChainManager } from './dhChain.js';
import { robots } from './robots.js';
import { UIControls } from './ui-controls.js';
import { RobotEditor } from './robot-editor.js';
import { initializeTabs, switchToTab } from './tabs.js';

/**
 * DHVisualizer Application
 */
class DHVisualizer {
    constructor() {
        this.threeSetup = null;
        this.chainManager = null;
        this.uiControls = null;
        this.robotEditor = null;
        this.customRobots = {}; // Store user-created robots
        
        this.init();
    }

    async loadBundledRobots() {
        try {
            const response = await fetch('./assets/default-robot.json');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const robot = await response.json();
            if (!robot || !robot.id || !Array.isArray(robot.chains)) {
                throw new Error('Invalid bundled robot JSON');
            }

            return {
                [robot.id]: {
                    ...robot,
                    isCustom: false,
                    description: robot.description || 'Bundled TerrestraX robot configuration'
                }
            };
        } catch (error) {
            console.warn('Bundled default robot could not be loaded:', error);
            return {};
        }
    }

    /**
     * Initialize the application
     */
    async init() {
        console.log('Initializing DH Visualizer (Multi-Chain)...');
        
        // Initialize tab navigation
        initializeTabs();
        
        // Get viewport container
        const viewport = document.getElementById('viewport');
        if (!viewport) {
            console.error('Viewport element not found!');
            return;
        }
        
        // Initialize Three.js scene
        this.threeSetup = new ThreeSetup(viewport);
        console.log('Three.js scene initialized');
        
        // Initialize chain manager
        this.chainManager = new ChainManager(this.threeSetup.getScene());
        console.log('Chain manager initialized');
        
        // Combine built-in, bundled, and custom robots.
        const bundledRobots = await this.loadBundledRobots();
        const allRobots = { ...robots, ...bundledRobots, ...this.customRobots };
        
        // Initialize UI controls
        this.uiControls = new UIControls(this.chainManager, allRobots);
        console.log('UI controls initialized');
        
        // Initialize robot editor
        this.robotEditor = new RobotEditor(this.uiControls, this.customRobots);
        console.log('Robot editor initialized');
        
        // Make robot editor globally accessible for button callbacks
        window.robotEditor = this.robotEditor;
        
        // Make threeSetup globally accessible for ragdoll mode
        window.threeSetup = this.threeSetup;
        
        console.log('DH Visualizer ready!');
        console.log('Available robots:', Object.keys(allRobots));
        if (bundledRobots.quadruped_spider) {
            this.uiControls.robotSelect.value = 'quadruped_spider';
            this.uiControls.onRobotChange('quadruped_spider');
        }
        console.log('💡 Click "New Robot" to create your own DH tables!');
        console.log('💡 Enable "Ragdoll Mode" to drag end-effectors in 3D (G=translate, R=rotate)');
    }

    /**
     * Get Three.js scene
     * @returns {THREE.Scene}
     */
    getScene() {
        return this.threeSetup ? this.threeSetup.getScene() : null;
    }

    /**
     * Get chain manager
     * @returns {ChainManager}
     */
    getChainManager() {
        return this.chainManager;
    }

    /**
     * Get UI controls
     * @returns {UIControls}
     */
    getUIControls() {
        return this.uiControls;
    }

    /**
     * Dispose of all resources
     */
    dispose() {
        if (this.chainManager) {
            this.chainManager.removeAllChains();
        }
        
        if (this.threeSetup) {
            this.threeSetup.dispose();
        }
        
        console.log('DH Visualizer disposed');
    }
}

// Initialize application when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.dhVisualizer = new DHVisualizer();
    });
} else {
    window.dhVisualizer = new DHVisualizer();
}

// Export for external access
export default DHVisualizer;
