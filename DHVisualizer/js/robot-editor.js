// robot-editor.js
// Robot creation and DH table editing functionality

import { degToRad, radToDeg } from './math.js';
import { exportToURDF, generateRVizLaunch, generateMoveItConfig, downloadFile } from './urdf-utils.js';

/**
 * RobotEditor class for creating and editing robots and DH parameters
 */
export class RobotEditor {
    constructor(uiControls, customRobots) {
        this.uiControls = uiControls;
        this.customRobots = customRobots; // Reference to custom robots object
        this.editMode = false;
        
        // Modal elements
        this.newRobotModal = document.getElementById('newRobotModal');
        this.newChainModal = document.getElementById('newChainModal');
        
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.attachEventListeners();
            });
        } else {
            this.attachEventListeners();
        }
    }

    attachEventListeners() {
        // Verify elements exist
        const elements = {
            newRobotBtn: document.getElementById('newRobotBtn'),
            createRobotBtn: document.getElementById('createRobotBtn'),
            cancelRobotBtn: document.getElementById('cancelRobotBtn'),
            exportRobotBtn: document.getElementById('exportRobotBtn'),
            importRobotBtn: document.getElementById('importRobotBtn'),
            importFileInput: document.getElementById('importFileInput'),
            addChainBtn: document.getElementById('addChainBtn'),
            addChainConfirmBtn: document.getElementById('addChainConfirmBtn'),
            cancelChainBtn: document.getElementById('cancelChainBtn')
        };

        // Check if elements exist
        for (const [key, element] of Object.entries(elements)) {
            if (!element) {
                console.error(`Element not found: ${key}`);
            }
        }

        // New Robot button
        if (elements.newRobotBtn) {
            elements.newRobotBtn.addEventListener('click', () => {
                console.log('New Robot button clicked');
                this.showNewRobotModal();
            });
        }

        // Create Robot button
        if (elements.createRobotBtn) {
            elements.createRobotBtn.addEventListener('click', () => {
                console.log('Create Robot button clicked');
                this.createNewRobot();
            });
        }

        // Cancel Robot button
        if (elements.cancelRobotBtn) {
            elements.cancelRobotBtn.addEventListener('click', () => {
                this.hideNewRobotModal();
            });
        }

        // Add Chain button
        if (elements.addChainBtn) {
            elements.addChainBtn.addEventListener('click', () => {
                console.log('Add Chain button clicked');
                if (!this.uiControls.currentRobot) {
                    alert('Please create or select a robot first.');
                    return;
                }
                this.showNewChainModal();
            });
        }

        // Add Chain Confirm button
        if (elements.addChainConfirmBtn) {
            elements.addChainConfirmBtn.addEventListener('click', () => {
                this.addNewChain();
            });
        }

        // Cancel Chain button
        if (elements.cancelChainBtn) {
            elements.cancelChainBtn.addEventListener('click', () => {
                this.hideNewChainModal();
            });
        }

        // Export Robot button
        if (elements.exportRobotBtn) {
            elements.exportRobotBtn.addEventListener('click', () => {
                console.log('Export button clicked');
                this.exportCurrentRobot();
            });
        }

        // Import Robot button
        if (elements.importRobotBtn) {
            elements.importRobotBtn.addEventListener('click', () => {
                console.log('Import button clicked');
                if (elements.importFileInput) {
                    elements.importFileInput.click();
                }
            });
        }

        // Import File Input
        if (elements.importFileInput) {
            elements.importFileInput.addEventListener('change', (e) => {
                this.importRobot(e.target.files[0]);
            });
        }

        // Close modal on outside click
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        });
    }

    showNewRobotModal() {
        console.log('Showing new robot modal');
        if (!this.newRobotModal) {
            console.error('newRobotModal element not found!');
            alert('Error: Modal not found. Please refresh the page.');
            return;
        }
        this.newRobotModal.style.display = 'block';
        const nameInput = document.getElementById('newRobotName');
        const conventionSelect = document.getElementById('newRobotConvention');
        if (nameInput) nameInput.value = '';
        if (conventionSelect) conventionSelect.value = 'standard';
    }

    hideNewRobotModal() {
        this.newRobotModal.style.display = 'none';
    }

    createNewRobot() {
        const name = document.getElementById('newRobotName').value.trim();
        const convention = document.getElementById('newRobotConvention').value;

        if (!name) {
            alert('Please enter a robot name.');
            return;
        }

        // Generate unique ID
        const id = 'custom_' + name.toLowerCase().replace(/\\s+/g, '_') + '_' + Date.now();

        // Create new robot
        const newRobot = {
            name: name,
            convention: convention,
            description: 'Custom robot',
            chains: [],
            isCustom: true
        };

        // Add to custom robots
        this.customRobots[id] = newRobot;

        // Update UI
        this.uiControls.robots[id] = newRobot;
        this.uiControls.populateRobotSelector();

        // Select the new robot
        this.uiControls.robotSelect.value = id;
        this.uiControls.onRobotChange(id);

        this.hideNewRobotModal();

        alert(`Robot "${name}" created! Click "Add Chain" to add kinematic chains.`);
    }

    showNewChainModal() {
        this.newChainModal.style.display = 'block';
        document.getElementById('newChainId').value = '';
        document.getElementById('newChainName').value = '';
        document.getElementById('newChainJoints').value = '3';
        document.getElementById('baseX').value = '0';
        document.getElementById('baseY').value = '0';
        document.getElementById('baseZ').value = '0';
    }

    hideNewChainModal() {
        this.newChainModal.style.display = 'none';
    }

    addNewChain() {
        const chainId = document.getElementById('newChainId').value.trim();
        const chainName = document.getElementById('newChainName').value.trim();
        const numJoints = parseInt(document.getElementById('newChainJoints').value);
        const baseX = parseFloat(document.getElementById('baseX').value);
        const baseY = parseFloat(document.getElementById('baseY').value);
        const baseZ = parseFloat(document.getElementById('baseZ').value);

        if (!chainId || !chainName) {
            alert('Please enter chain ID and name.');
            return;
        }

        if (numJoints < 1 || numJoints > 10) {
            alert('Number of joints must be between 1 and 10.');
            return;
        }

        // Check if chain ID already exists
        if (this.uiControls.currentRobot.chains.find(c => c.id === chainId)) {
            alert('A chain with this ID already exists.');
            return;
        }

        // Create chain definition
        const newChain = {
            id: chainId,
            name: chainName,
            baseTransform: [
                [1, 0, 0, baseX],
                [0, 1, 0, baseY],
                [0, 0, 1, baseZ],
                [0, 0, 0, 1]
            ],
            joints: []
        };

        // Create default joints
        for (let i = 0; i < numJoints; i++) {
            newChain.joints.push({
                a: 0.1,
                alpha: 0,
                d: 0,
                theta: 0,
                visible: true,
                isPrismatic: false
            });
        }

        // Add chain to current robot
        this.uiControls.currentRobot.chains.push(newChain);

        // Refresh UI
        this.uiControls.chainManager.addChain(newChain);
        this.uiControls.buildChainList();
        this.uiControls.buildDHTables();
        this.uiControls.buildTaskSpaceControls();

        this.hideNewChainModal();

        alert(`Chain "${chainName}" added! Use Edit Mode to adjust DH parameters.`);
    }

    toggleEditMode() {
        this.editMode = !this.editMode;
        const btn = document.getElementById('editModeBtn');
        const dhTables = document.getElementById('dhTables');

        if (this.editMode) {
            btn.textContent = '💾 Save Changes';
            btn.style.background = '#4CAF50';
            dhTables.classList.add('edit-mode');
            this.enableEditing();
        } else {
            btn.textContent = '✏️ Edit Mode';
            btn.style.background = '#FF9800';
            dhTables.classList.remove('edit-mode');
            this.saveChanges();
        }
    }

    enableEditing() {
        // Add edit buttons to chains and joints
        const chainTables = document.querySelectorAll('.dh-chain-table');
        
        chainTables.forEach(table => {
            const chainId = table.id.replace('dh-table-', '');
            const title = table.querySelector('h4');
            
            // Add chain actions if not exists
            if (!title.querySelector('.chain-actions')) {
                const actions = document.createElement('div');
                actions.className = 'chain-actions';
                actions.innerHTML = `
                    <button onclick="window.robotEditor.addJoint('${chainId}')">➕ Joint</button>
                    <button onclick="window.robotEditor.deleteChain('${chainId}')">🗑️ Chain</button>
                `;
                title.appendChild(actions);
            }

            // Add joint delete buttons
            const joints = table.querySelectorAll('.dh-row:not(.dh-row-header)');
            joints.forEach((row, index) => {
                if (!row.querySelector('.joint-actions')) {
                    const actions = document.createElement('div');
                    actions.className = 'joint-actions';
                    actions.innerHTML = `
                        <button onclick="window.robotEditor.deleteJoint('${chainId}', ${index})">✖</button>
                    `;
                    row.appendChild(actions);
                }
            });
        });
    }

    saveChanges() {
        // Collect all changes from input fields
        const chainTables = document.querySelectorAll('.dh-chain-table');
        
        chainTables.forEach(table => {
            const chainId = table.id.replace('dh-table-', '');
            const chain = this.uiControls.currentRobot.chains.find(c => c.id === chainId);
            
            if (!chain) return;

            // Update joint parameters from inputs
            const paramInputs = table.querySelectorAll('.dh-param-input');
            paramInputs.forEach(input => {
                const [, , jointIdx, param] = input.id.split('-');
                const index = parseInt(jointIdx);
                const value = parseFloat(input.value);

                if (param === 'a') {
                    chain.joints[index].a = value;
                } else if (param === 'alpha') {
                    chain.joints[index].alpha = degToRad(value);
                } else if (param === 'd') {
                    chain.joints[index].d = value;
                }
            });

            // Update the chain in the chain manager
            const chainInstance = this.uiControls.chainManager.getChain(chainId);
            if (chainInstance) {
                chainInstance.joints = JSON.parse(JSON.stringify(chain.joints));
                chainInstance.updateFK();
            }
        });

        // Remove action buttons
        document.querySelectorAll('.chain-actions, .joint-actions').forEach(el => el.remove());

        alert('Changes saved! The 3D view has been updated.');
    }

    addJoint(chainId) {
        const chain = this.uiControls.currentRobot.chains.find(c => c.id === chainId);
        if (!chain) return;

        chain.joints.push({
            a: 0.1,
            alpha: 0,
            d: 0,
            theta: 0,
            visible: true,
            isPrismatic: false
        });

        // Rebuild UI
        this.uiControls.buildDHTables();
        this.uiControls.buildTaskSpaceControls();
        this.enableEditing();
    }

    deleteJoint(chainId, index) {
        if (!confirm('Delete this joint?')) return;

        const chain = this.uiControls.currentRobot.chains.find(c => c.id === chainId);
        if (!chain) return;

        chain.joints.splice(index, 1);

        // Rebuild UI
        this.uiControls.buildDHTables();
        this.uiControls.buildTaskSpaceControls();
        this.enableEditing();
    }

    deleteChain(chainId) {
        if (!confirm('Delete this entire chain?')) return;

        const idx = this.uiControls.currentRobot.chains.findIndex(c => c.id === chainId);
        if (idx === -1) return;

        this.uiControls.currentRobot.chains.splice(idx, 1);
        this.uiControls.chainManager.removeChain(chainId);

        // Rebuild UI
        this.uiControls.buildChainList();
        this.uiControls.buildDHTables();
        this.uiControls.buildTaskSpaceControls();
    }

    /**
     * Build a live snapshot of the current robot state by reading from
     * the active DHChain instances (which hold the ground-truth joint data)
     * and falling back to the robot definition for metadata.
     */
    buildLiveSnapshot() {
        const robot = this.uiControls.currentRobot;
        const robotId = this.uiControls.robotSelect.value;

        const liveChains = robot.chains.map(chainDef => {
            const chainInstance = this.uiControls.chainManager.getChain(chainDef.id);

            // Deep-copy the live DHChain joints (ground-truth)
            const liveJoints = chainInstance
                ? JSON.parse(JSON.stringify(chainInstance.joints))
                : JSON.parse(JSON.stringify(chainDef.joints));

            // Capture current actuated joint angles separately.
            // DHChain stores: joint.theta = fixed offset, jointAngles[i] = variable.
            // FK computes: theta_total = joint.theta + jointAngles[i].
            // We store both so import can restore the exact pose.
            let currentAngles = null;
            if (chainInstance) {
                const angles = chainInstance.getJointAngles();
                // Only store if any non-zero
                if (angles.some(a => a !== 0)) {
                    currentAngles = angles;
                }
            }

            // Read live base transform from the chain instance if available
            const liveBase = chainInstance && chainInstance.baseTransform
                ? JSON.parse(JSON.stringify(chainInstance.baseTransform))
                : (chainDef.baseTransform || [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]);

            const chainData = {
                id: chainDef.id,
                name: chainDef.name,
                baseTransform: liveBase,
                joints: liveJoints
            };

            // Store current joint angles so the pose is fully reproducible on import
            if (currentAngles) {
                chainData.jointAngles = currentAngles;
            }

            return chainData;
        });

        return {
            id: robotId,
            name: robot.name,
            convention: robot.convention || 'standard',
            description: robot.description || '',
            chains: liveChains,
            isCustom: true,
            exportDate: new Date().toISOString()
        };
    }

    exportCurrentRobot() {
        if (!this.uiControls.currentRobot) {
            alert('Please select or create a robot first.');
            return;
        }

        // Build from live DHChain state — not the potentially stale definition
        const exportData = this.buildLiveSnapshot();

        // Ask user which format to export
        const format = prompt('Export format:\n1 - JSON (default)\n2 - URDF\n3 - Both\n\nEnter number:', '1');
        
        if (format === '2' || format === '3') {
            // Export URDF
            const urdf = exportToURDF(exportData);
            const robotName = exportData.name.replace(/\s+/g, '_').toLowerCase();
            downloadFile(`${robotName}.urdf`, urdf);
            
            // Also export RViz launch file
            const launchFile = generateRVizLaunch(robotName);
            downloadFile(`${robotName}_rviz.launch`, launchFile);
            
            // Export MoveIt config info
            const moveitConfig = generateMoveItConfig(robotName);
            downloadFile(`${robotName}_moveit_package.xml`, moveitConfig.packageXml);
            downloadFile(`${robotName}_README.md`, moveitConfig.readme);
            
            console.log('URDF and ROS files exported!');
        }
        
        if (format === '1' || format === '3' || !format) {
            // Export JSON (original behavior)
            const json = JSON.stringify(exportData, null, 2);
            const blob = new Blob([json], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const robotName = exportData.name.replace(/\s+/g, '_').toLowerCase();
            a.download = `${robotName}_robot.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            console.log('Robot exported as JSON:', exportData);
        }
    }

    importRobot(file) {
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                
                // Validate structure
                if (!data.name || !data.chains) {
                    throw new Error('Invalid robot file format');
                }

                // Generate new ID if needed
                const id = data.id || ('imported_' + Date.now());
                
                // Add to custom robots
                this.customRobots[id] = {
                    name: data.name,
                    convention: data.convention || 'standard',
                    description: data.description || 'Imported robot',
                    chains: data.chains,
                    isCustom: true
                };

                // Update UI
                this.uiControls.robots[id] = this.customRobots[id];
                this.uiControls.populateRobotSelector();

                // Select the imported robot
                this.uiControls.robotSelect.value = id;
                this.uiControls.onRobotChange(id);

                // Restore saved joint angles (the variable part of actuated joints)
                data.chains.forEach(chain => {
                    if (chain.jointAngles) {
                        const chainInstance = this.uiControls.chainManager.getChain(chain.id);
                        if (chainInstance) {
                            chainInstance.setAllJointAngles(chain.jointAngles);
                            chainInstance.updateVisualization();
                        }
                    }
                });

                // Rebuild UI to reflect restored angles (sliders, inputs, etc.)
                this.uiControls.buildDHTables();
                this.uiControls.buildTaskSpaceControls();

                alert(`Robot "${data.name}" imported successfully!`);
            } catch (error) {
                alert('Error importing robot: ' + error.message);
            }
        };
        
        reader.readAsText(file);
        
        // Reset file input
        document.getElementById('importFileInput').value = '';
    }
}
