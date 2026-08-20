// ui-controls.js
// Dynamic UI generation and control handling

import { degToRad, radToDeg, computeIK } from './math.js';
import { switchToTab } from './tabs.js';

/**
 * UIControls class manages all UI elements and interactions
 */
export class UIControls {
    constructor(chainManager, robots) {
        this.chainManager = chainManager;
        this.robots = robots;
        this.currentRobot = null;
        
        // DOM elements
        this.robotSelect = document.getElementById('robotSelect');
        this.chainList = document.getElementById('chainList');
        this.dhTables = document.getElementById('dhTables');
        this.taskSpaceControls = document.getElementById('taskSpaceControls');
        this.showAllBtn = document.getElementById('showAllChains');
        this.hideAllBtn = document.getElementById('hideAllChains');
        
        // State
        this.activeChains = new Set(); // Set of active chain IDs
        this.pythonExportMode = new Map(); // Map<chainId, 'numeric' | 'sympy'> - tracks export mode per chain
        
        this.init();
    }

    /**
     * Initialize UI
     */
    init() {
        this.populateRobotSelector();
        this.attachGlobalEventListeners();
    }

    /**
     * Populate robot selector dropdown
     */
    populateRobotSelector() {
        // Clear existing options
        this.robotSelect.innerHTML = '<option value="">Select a robot...</option>';
        
        // Add robots
        Object.entries(this.robots).forEach(([id, robot]) => {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = robot.name;
            this.robotSelect.appendChild(option);
        });
    }

    /**
     * Attach global event listeners
     */
    attachGlobalEventListeners() {
        // Robot selection
        this.robotSelect.addEventListener('change', (e) => {
            this.onRobotChange(e.target.value);
        });
        
        // Show/hide all buttons
        this.showAllBtn.addEventListener('click', () => {
            this.showAllChains();
        });
        
        this.hideAllBtn.addEventListener('click', () => {
            this.hideAllChains();
        });
    }

    /**
     * Handle robot selection change
     * @param {string} robotId 
     */
    onRobotChange(robotId) {
        // Clear existing chains
        this.chainManager.removeAllChains();
        this.activeChains.clear();
        
        if (!robotId) {
            this.clearUI();
            this.currentRobot = null;
            return;
        }
        
        // Load new robot
        this.currentRobot = this.robots[robotId];
        
        if (!this.currentRobot) {
            console.error('Robot not found:', robotId);
            return;
        }
        
        // Update chain manager convention
        this.chainManager.setConvention(this.currentRobot.convention || 'standard');
        
        // Create chains
        this.currentRobot.chains.forEach(chainDef => {
            this.chainManager.addChain(chainDef);
        });
        
        // Rebuild UI
        this.buildChainList();
        this.buildDHTables();
        this.buildTaskSpaceControls();
    }

    /**
     * Clear all UI elements
     */
    clearUI() {
        this.chainList.innerHTML = '';
        this.dhTables.innerHTML = '';
        this.taskSpaceControls.innerHTML = '';
    }

    /**
     * Build chain list with checkboxes
     */
    buildChainList() {
        this.chainList.innerHTML = '';
        
        if (!this.currentRobot) return;
        
        this.currentRobot.chains.forEach(chainDef => {
            const chainDiv = document.createElement('div');
            chainDiv.className = 'chain-checkbox';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `chain-${chainDef.id}`;
            checkbox.checked = false;
            
            const label = document.createElement('label');
            label.htmlFor = `chain-${chainDef.id}`;
            label.textContent = chainDef.name;
            
            checkbox.addEventListener('change', (e) => {
                this.onChainToggle(chainDef.id, e.target.checked);
            });
            
            chainDiv.appendChild(checkbox);
            chainDiv.appendChild(label);
            this.chainList.appendChild(chainDiv);
        });
    }

    /**
     * Handle chain toggle
     * @param {string} chainId 
     * @param {boolean} active 
     */
    onChainToggle(chainId, active) {
        const chain = this.chainManager.getChain(chainId);
        if (!chain) return;
        
        if (active) {
            this.activeChains.add(chainId);
            chain.show();
            this.showDHTable(chainId);
            this.showTaskSpace(chainId);
        } else {
            this.activeChains.delete(chainId);
            chain.hide();
            this.hideDHTable(chainId);
            this.hideTaskSpace(chainId);
        }
    }

    /**
     * Build DH parameter tables for all chains
     */
    buildDHTables() {
        this.dhTables.innerHTML = '';
        
        if (!this.currentRobot) return;
        
        this.currentRobot.chains.forEach(chainDef => {
            const tableDiv = this.createDHTable(chainDef);
            // Show table if chain is active, hide otherwise
            const isActive = this.activeChains.has(chainDef.id);
            tableDiv.style.display = isActive ? 'block' : 'none';
            this.dhTables.appendChild(tableDiv);
        });
    }

    /**
     * Create DH table for a single chain
     * @param {Object} chainDef 
     * @returns {HTMLElement}
     */
    createDHTable(chainDef) {
        const container = document.createElement('div');
        container.className = 'dh-chain-table';
        container.id = `dh-table-${chainDef.id}`;
        
        const header = document.createElement('div');
        header.style.cssText = 'display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;';
        
        const title = document.createElement('h4');
        title.textContent = `${chainDef.name} (${chainDef.id})`;
        title.style.margin = '0';
        
        const addJointBtn = document.createElement('button');
        addJointBtn.textContent = '+ Add Joint';
        addJointBtn.style.cssText = 'padding: 4px 12px; font-size: 12px;';
        addJointBtn.addEventListener('click', () => {
            this.addJointToChain(chainDef.id, false);
        });
        
        const addVirtualBtn = document.createElement('button');
        addVirtualBtn.textContent = '+ Virtual';
        addVirtualBtn.style.cssText = 'padding: 4px 12px; font-size: 12px;';
        addVirtualBtn.title = 'Add virtual joint for frame alignment';
        addVirtualBtn.addEventListener('click', () => {
            this.addJointToChain(chainDef.id, true);
        });
        
        const btnGroup = document.createElement('div');
        btnGroup.style.cssText = 'display: flex; gap: 5px;';
        btnGroup.appendChild(addJointBtn);
        btnGroup.appendChild(addVirtualBtn);
        
        header.appendChild(title);
        header.appendChild(btnGroup);
        container.appendChild(header);
        
        // Add base position controls
        const basePositionDiv = document.createElement('div');
        basePositionDiv.style.cssText = 'display: flex; align-items: center; gap: 10px; margin-bottom: 10px; padding: 8px; background: rgba(139, 111, 71, 0.05); border-radius: 6px;';
        
        const baseLabel = document.createElement('span');
        baseLabel.textContent = 'Base Position:';
        baseLabel.style.cssText = 'font-weight: 600; font-size: 12px;';
        basePositionDiv.appendChild(baseLabel);
        
        // Extract current base position from baseTransform matrix (Z-up coordinates)
        const basePos = {
            x: chainDef.baseTransform[0][3],
            y: chainDef.baseTransform[1][3],
            z: chainDef.baseTransform[2][3]
        };
        
        ['x', 'y', 'z'].forEach(axis => {
            const group = document.createElement('div');
            group.style.cssText = 'display: flex; align-items: center; gap: 4px;';
            
            const axisLabel = document.createElement('span');
            axisLabel.textContent = axis.toUpperCase() + ':';
            axisLabel.style.cssText = 'font-size: 11px; font-weight: 600;';
            
            const input = document.createElement('input');
            input.type = 'number';
            input.step = '0.01';
            input.value = basePos[axis].toFixed(3);
            input.className = 'table-input';
            input.style.width = '70px';
            input.addEventListener('change', (e) => {
                this.onBasePositionChange(chainDef.id, axis, parseFloat(e.target.value));
            });
            
            group.appendChild(axisLabel);
            group.appendChild(input);
            basePositionDiv.appendChild(group);
        });
        
        container.appendChild(basePositionDiv);
        
        // Create HTML table
        const table = document.createElement('table');
        table.className = 'dh-table';
        table.id = `table-${chainDef.id}`;
        
        // Table header
        const thead = document.createElement('thead');
        thead.innerHTML = `
            <tr>
                <th>Joint</th>
                <th>Type</th>
                <th>θ (deg)</th>
                <th>d (m)</th>
                <th>a (m)</th>
                <th>α (deg)</th>
                <th>Virtual</th>
                <th>Show</th>
                <th>Action</th>
            </tr>
        `;
        table.appendChild(thead);
        
        // Table body
        const tbody = document.createElement('tbody');
        tbody.id = `tbody-${chainDef.id}`;
        
        chainDef.joints.forEach((joint, index) => {
            const row = this.createJointTableRow(chainDef.id, index, joint);
            tbody.appendChild(row);
        });
        
        table.appendChild(tbody);
        container.appendChild(table);
        
        // Add Python code preview section (collapsible)
        const pythonSection = document.createElement('div');
        pythonSection.style.cssText = 'margin-top: 15px;';
        
        const pythonHeader = document.createElement('div');
        pythonHeader.style.cssText = 'display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: rgba(139, 111, 71, 0.1); backdrop-filter: blur(10px); border-radius: 8px; cursor: pointer; transition: background 0.2s;';
        pythonHeader.onmouseover = () => pythonHeader.style.background = 'rgba(139, 111, 71, 0.15)';
        pythonHeader.onmouseout = () => pythonHeader.style.background = 'rgba(139, 111, 71, 0.1)';
        
        const pythonTitle = document.createElement('span');
        pythonTitle.textContent = '🐍 Python Function';
        pythonTitle.style.cssText = 'font-weight: 600; font-size: 13px;';
        
        const pythonToggle = document.createElement('span');
        pythonToggle.textContent = '▼';
        pythonToggle.style.cssText = 'font-size: 12px; transition: transform 0.3s;';
        pythonToggle.id = `python-toggle-${chainDef.id}`;
        
        pythonHeader.appendChild(pythonTitle);
        pythonHeader.appendChild(pythonToggle);
        
        const pythonContent = document.createElement('div');
        pythonContent.id = `python-content-${chainDef.id}`;
        pythonContent.style.cssText = 'max-height: 0; overflow: hidden; transition: max-height 0.3s ease;';
        
        const pythonInner = document.createElement('div');
        pythonInner.style.cssText = 'padding: 12px; background: rgba(0, 0, 0, 0.3); backdrop-filter: blur(20px); border-radius: 0 0 8px 8px; margin-top: -4px; display: flex; flex-direction: column;';
        
        // Scrollable content area for code
        const scrollContainer = document.createElement('div');
        scrollContainer.style.cssText = 'max-height: 500px; overflow-y: auto; margin-bottom: 10px;';
        
        // Export mode selector
        const modeContainer = document.createElement('div');
        modeContainer.style.cssText = 'display: flex; gap: 8px; margin-bottom: 10px; align-items: center;';
        
        const modeLabel = document.createElement('span');
        modeLabel.textContent = 'Export:';
        modeLabel.style.cssText = 'font-size: 11px; color: #aaa;';
        
        const numericBtn = document.createElement('button');
        numericBtn.textContent = 'Numeric';
        numericBtn.id = `mode-numeric-${chainDef.id}`;
        numericBtn.style.cssText = 'padding: 4px 10px; font-size: 11px; background: var(--accent); color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: 500;';
        numericBtn.onclick = () => this.switchPythonMode(chainDef.id, 'numeric');
        
        const sympyBtn = document.createElement('button');
        sympyBtn.textContent = 'SymPy';
        sympyBtn.id = `mode-sympy-${chainDef.id}`;
        sympyBtn.style.cssText = 'padding: 4px 10px; font-size: 11px; background: rgba(255, 255, 255, 0.1); color: #aaa; border: none; border-radius: 4px; cursor: pointer;';
        sympyBtn.onclick = () => this.switchPythonMode(chainDef.id, 'sympy');
        
        modeContainer.appendChild(modeLabel);
        modeContainer.appendChild(numericBtn);
        modeContainer.appendChild(sympyBtn);
        
        const codeBlock = document.createElement('pre');
        codeBlock.id = `python-code-${chainDef.id}`;
        codeBlock.style.cssText = 'margin: 0; padding: 12px; background: rgba(0, 0, 0, 0.4); border-radius: 6px; font-family: "Consolas", "Monaco", monospace; font-size: 11px; line-height: 1.5; color: #e0e0e0; white-space: pre-wrap; word-wrap: break-word;';
        
        const copyBtn = document.createElement('button');
        copyBtn.textContent = '📋 Copy to Clipboard';
        copyBtn.style.cssText = 'padding: 6px 14px; font-size: 12px; background: var(--accent); color: white; border: none; border-radius: 6px; cursor: pointer; align-self: flex-start;';
        copyBtn.onclick = () => this.copyChainToPython(chainDef.id);
        
        scrollContainer.appendChild(modeContainer);
        scrollContainer.appendChild(codeBlock);
        
        pythonInner.appendChild(scrollContainer);
        pythonInner.appendChild(copyBtn);
        pythonContent.appendChild(pythonInner);
        
        pythonHeader.onclick = () => {
            const content = pythonContent;
            const toggle = pythonToggle;
            if (content.style.maxHeight === '0px' || !content.style.maxHeight) {
                content.style.maxHeight = '650px';
                toggle.style.transform = 'rotate(180deg)';
                // Default to numeric mode if not set
                if (!this.pythonExportMode.has(chainDef.id)) {
                    this.pythonExportMode.set(chainDef.id, 'numeric');
                }
                this.updatePythonCodeDisplay(chainDef.id);
            } else {
                content.style.maxHeight = '0';
                toggle.style.transform = 'rotate(0deg)';
            }
        };
        
        pythonSection.appendChild(pythonHeader);
        pythonSection.appendChild(pythonContent);
        container.appendChild(pythonSection);
        
        return container;
    }

    /**
     * Create a single joint parameter row in table format
     * @param {string} chainId 
     * @param {number} index 
     * @param {Object} joint 
     * @returns {HTMLElement}
     */
    createJointTableRow(chainId, index, joint) {
        const row = document.createElement('tr');
        row.id = `row-${chainId}-${index}`;
        
        const isVirtual = joint.virtual || false;
        const jointType = joint.joint_type || 'revolute';
        
        // Style row if virtual
        if (isVirtual) {
            row.style.backgroundColor = 'var(--bg-tertiary)';
            row.style.opacity = '0.7';
        }
        
        // Joint number
        const jointCell = document.createElement('td');
        jointCell.textContent = isVirtual ? `V${index + 1}` : `J${index + 1}`;
        jointCell.style.fontWeight = 'bold';
        if (isVirtual) {
            jointCell.style.fontStyle = 'italic';
            jointCell.style.color = 'var(--text-muted)';
        }
        row.appendChild(jointCell);
        
        // Joint type dropdown (only for real joints)
        const typeCell = document.createElement('td');
        if (isVirtual) {
            typeCell.textContent = 'Frame';
            typeCell.style.fontStyle = 'italic';
            typeCell.style.color = 'var(--text-muted)';
        } else {
            const typeSelect = document.createElement('select');
            typeSelect.className = 'table-input';
            typeSelect.style.width = '90px';
            typeSelect.innerHTML = `
                <option value="revolute" ${jointType === 'revolute' ? 'selected' : ''}>Revolute</option>
                <option value="prismatic" ${jointType === 'prismatic' ? 'selected' : ''}>Prismatic</option>
                <option value="fixed" ${jointType === 'fixed' ? 'selected' : ''}>Fixed</option>
            `;
            typeSelect.addEventListener('change', (e) => {
                this.onJointTypeChange(chainId, index, e.target.value);
            });
            typeCell.appendChild(typeSelect);
        }
        row.appendChild(typeCell);
        
        // Theta (slider + input)
        const thetaCell = document.createElement('td');
        thetaCell.style.whiteSpace = 'nowrap';
        const thetaContainer = document.createElement('div');
        thetaContainer.style.cssText = 'display: flex; align-items: center; gap: 5px; justify-content: center;';
        
        const thetaSlider = document.createElement('input');
        thetaSlider.type = 'range';
        thetaSlider.min = '-180';
        thetaSlider.max = '180';
        thetaSlider.step = '1';
        
        // For actuated joints, the displayed angle should include the variable part
        // stored in chainInstance.jointAngles[index], not just the fixed offset.
        let displayTheta = joint.theta;
        if (!joint.virtual) {
            const chainInstance = this.chainManager.getChain(chainId);
            if (chainInstance) {
                const angles = chainInstance.getJointAngles();
                displayTheta = joint.theta + (angles[index] || 0);
            }
        }
        
        thetaSlider.value = radToDeg(displayTheta).toFixed(0);
        thetaSlider.id = `slider-${chainId}-${index}`;
        thetaSlider.style.width = '100px';
        thetaSlider.style.flexShrink = '0';
        // Virtual joints can have theta for Z-rotation alignment
        
        const thetaInput = document.createElement('input');
        thetaInput.type = 'number';
        thetaInput.min = '-180';
        thetaInput.max = '180';
        thetaInput.step = '1';
        thetaInput.value = radToDeg(displayTheta).toFixed(0);
        thetaInput.id = `number-${chainId}-${index}`;
        thetaInput.style.width = '60px';
        thetaInput.className = 'table-input';
        // Virtual joints can have theta for Z-rotation alignment
        
        thetaSlider.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value);
            thetaInput.value = value;
            this.onJointAngleChange(chainId, index, degToRad(value));
        });
        
        thetaInput.addEventListener('change', (e) => {
            const value = parseFloat(e.target.value);
            thetaSlider.value = value;
            this.onJointAngleChange(chainId, index, degToRad(value));
        });
        
        thetaContainer.appendChild(thetaSlider);
        thetaContainer.appendChild(thetaInput);
        thetaCell.appendChild(thetaContainer);
        row.appendChild(thetaCell);
        
        // d, a, alpha (editable inputs)
        const params = [
            { key: 'd', value: joint.d, step: '0.001' },
            { key: 'a', value: joint.a, step: '0.001' },
            { key: 'alpha', value: radToDeg(joint.alpha), step: '1' }
        ];
        
        params.forEach(param => {
            const cell = document.createElement('td');
            const input = document.createElement('input');
            input.type = 'number';
            input.step = param.step;
            input.value = param.value.toFixed(param.key === 'alpha' ? 2 : 4);
            input.className = 'table-input';
            input.id = `param-${chainId}-${index}-${param.key}`;
            
            input.addEventListener('change', (e) => {
                this.onDHParamChange(chainId, index, param.key, parseFloat(e.target.value));
            });
            
            cell.appendChild(input);
            row.appendChild(cell);
        });
        
        // Virtual joint checkbox
        const virtualCell = document.createElement('td');
        virtualCell.style.textAlign = 'center';
        virtualCell.style.padding = '10px';
        const virtualCheck = document.createElement('input');
        virtualCheck.type = 'checkbox';
        virtualCheck.checked = isVirtual;
        virtualCheck.id = `virtual-${chainId}-${index}`;
        virtualCheck.title = 'Virtual joints are for frame alignment (all parameters editable, not exported as actuated joints)';
        virtualCheck.style.width = '18px';
        virtualCheck.style.height = '18px';
        virtualCheck.style.cursor = 'pointer';
        virtualCheck.addEventListener('change', (e) => {
            this.onVirtualJointChange(chainId, index, e.target.checked);
        });
        virtualCell.appendChild(virtualCheck);
        row.appendChild(virtualCell);
        
        // Visibility checkbox
        const visCell = document.createElement('td');
        visCell.style.textAlign = 'center';
        visCell.style.padding = '10px';
        const visCheck = document.createElement('input');
        visCheck.type = 'checkbox';
        visCheck.checked = joint.visible;
        visCheck.id = `vis-${chainId}-${index}`;
        visCheck.style.width = '18px';
        visCheck.style.height = '18px';
        visCheck.style.cursor = 'pointer';
        visCheck.addEventListener('change', (e) => {
            this.onFrameVisibilityChange(chainId, index, e.target.checked);
        });
        visCell.appendChild(visCheck);
        row.appendChild(visCell);
        
        // Delete button
        const actionCell = document.createElement('td');
        actionCell.style.textAlign = 'center';
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Delete';
        deleteBtn.style.cssText = 'padding: 4px 10px; font-size: 11px;';
        deleteBtn.addEventListener('click', () => {
            this.deleteJoint(chainId, index);
        });

        const insertAboveBtn = document.createElement('button');
        insertAboveBtn.textContent = '↑ Insert';
        insertAboveBtn.title = 'Insert a joint above this row';
        insertAboveBtn.style.cssText = 'padding: 4px 8px; font-size: 11px;';
        insertAboveBtn.addEventListener('click', () => {
            this.addJointToChain(chainId, false, index);
        });

        actionCell.style.cssText = 'text-align: center; display: flex; gap: 4px; justify-content: center;';
        actionCell.appendChild(insertAboveBtn);
        actionCell.appendChild(deleteBtn);
        row.appendChild(actionCell);
        
        return row;
    }

    /**
     * Handle joint angle change
     * @param {string} chainId 
     * @param {number} index 
     * @param {number} angle - in radians
     */
    onJointAngleChange(chainId, index, angle) {
        const chain = this.chainManager.getChain(chainId);
        if (!chain) return;
        
        const joint = chain.joints[index];
        
        if (joint.virtual) {
            // For virtual joints, update the base theta value (fixed DH parameter)
            joint.theta = angle;
            
            // Also update robot definition
            const chainDef = this.currentRobot.chains.find(c => c.id === chainId);
            if (chainDef) {
                chainDef.joints[index].theta = angle;
            }
            
            // Update FK and visualization
            chain.updateFK();
            chain.updateVisualization();
        } else {
            // For real joints, update the variable angle (joint actuation)
            // The slider/input shows the total angle (offset + variable),
            // but setJointAngle stores only the variable part.
            // FK computes: theta_total = joint.theta(offset) + jointAngles[i](variable)
            const variableAngle = angle - joint.theta;
            chain.setJointAngle(index, variableAngle);
        }
        
        this.updateTaskSpaceDisplay(chainId);
        this.updatePythonCodeDisplay(chainId);
    }
    
    /**
     * Handle joint type change
     * @param {string} chainId 
     * @param {number} index 
     * @param {string} type - 'revolute', 'prismatic', or 'fixed'
     */
    onJointTypeChange(chainId, index, type) {
        const chain = this.chainManager.getChain(chainId);
        if (!chain) return;
        
        chain.joints[index].joint_type = type;
        
        // Update robot definition
        const chainDef = this.currentRobot.chains.find(c => c.id === chainId);
        if (chainDef) {
            chainDef.joints[index].joint_type = type;
        }
        
        // If fixed, treat like virtual joint
        if (type === 'fixed') {
            chain.joints[index].theta = 0;
            const slider = document.getElementById(`slider-${chainId}-${index}`);
            const input = document.getElementById(`number-${chainId}-${index}`);
            if (slider) {
                slider.value = '0';
                slider.disabled = true;
            }
            if (input) {
                input.value = '0';
                input.disabled = true;
            }
        } else {
            // Re-enable controls
            const slider = document.getElementById(`slider-${chainId}-${index}`);
            const input = document.getElementById(`number-${chainId}-${index}`);
            if (slider) slider.disabled = false;
            if (input) input.disabled = false;
        }
        
        chain.updateFK();
        chain.updateVisualization();
        this.updateTaskSpaceDisplay(chainId);
    }
    
    /**
     * Handle virtual joint checkbox change
     * @param {string} chainId 
     * @param {number} index 
     * @param {boolean} isVirtual 
     */
    onVirtualJointChange(chainId, index, isVirtual) {
        const chain = this.chainManager.getChain(chainId);
        if (!chain) return;
        
        chain.joints[index].virtual = isVirtual;
        
        // Don't reset theta or disable controls - virtual joints need theta for Z-rotation
        // They are just marked as 'fixed' type for URDF export
        
        // Update robot definition
        const chainDef = this.currentRobot.chains.find(c => c.id === chainId);
        if (chainDef) {
            chainDef.joints[index].virtual = isVirtual;
        }
        
        this.updatePythonCodeDisplay(chainId);
        
        // Rebuild row to update styling
        const tbody = document.getElementById(`tbody-${chainId}`);
        if (tbody) {
            const row = document.getElementById(`row-${chainId}-${index}`);
            if (row) {
                const newRow = this.createJointTableRow(chainId, index, chain.joints[index]);
                tbody.replaceChild(newRow, row);
            }
        }
        
        chain.updateFK();
        chain.updateVisualization();
        this.updateTaskSpaceDisplay(chainId);
    }

    /**
     * Handle frame visibility change
     * @param {string} chainId 
     * @param {number} index 
     * @param {boolean} visible 
     */
    onFrameVisibilityChange(chainId, index, visible) {
        const chain = this.chainManager.getChain(chainId);
        if (chain) {
            chain.setFrameVisible(index, visible);
        }
    }

    /**
     * Handle base position change
     * @param {string} chainId 
     * @param {string} axis - 'x', 'y', or 'z' (Z-up coordinates)
     * @param {number} value - new position value
     */
    onBasePositionChange(chainId, axis, value) {
        const chain = this.chainManager.getChain(chainId);
        if (!chain) return;
        
        // Update baseTransform matrix (Z-up coordinates)
        const axisIndex = { x: 0, y: 1, z: 2 }[axis];
        chain.baseTransform[axisIndex][3] = value;
        
        // Update robot definition
        const chainDef = this.currentRobot.chains.find(c => c.id === chainId);
        if (chainDef) {
            chainDef.baseTransform[axisIndex][3] = value;
        }
        
        // Recompute FK and update visualization
        chain.updateFK();
        chain.clearVisualization();
        chain.updateVisualization();
        
        this.updateTaskSpaceDisplay(chainId);
        this.updatePythonCodeDisplay(chainId);
    }

    /**
     * Show DH table for a specific chain
     * @param {string} chainId 
     */
    showDHTable(chainId) {
        const table = document.getElementById(`dh-table-${chainId}`);
        if (table) {
            table.style.display = 'block';
        }
    }

    /**
     * Hide DH table for a specific chain
     * @param {string} chainId 
     */
    hideDHTable(chainId) {
        const table = document.getElementById(`dh-table-${chainId}`);
        if (table) {
            table.style.display = 'none';
        }
    }

    /**
     * Build task space controls for all chains
     */
    buildTaskSpaceControls() {
        this.taskSpaceControls.innerHTML = '';
        
        if (!this.currentRobot) return;
        
        this.currentRobot.chains.forEach(chainDef => {
            const taskSpaceDiv = this.createTaskSpacePanel(chainDef);
            taskSpaceDiv.style.display = 'none'; // Hidden by default
            this.taskSpaceControls.appendChild(taskSpaceDiv);
        });
    }

    /**
     * Create task space panel for a single chain
     * @param {Object} chainDef 
     * @returns {HTMLElement}
     */
    createTaskSpacePanel(chainDef) {
        const container = document.createElement('div');
        container.className = 'task-space-chain';
        container.id = `task-space-${chainDef.id}`;
        
        const title = document.createElement('h4');
        title.textContent = `${chainDef.name} - End Effector`;
        container.appendChild(title);
        
        // Current EE position display
        const eeDiv = document.createElement('div');
        eeDiv.className = 'ee-position';
        eeDiv.id = `ee-pos-${chainDef.id}`;
        
        ['x', 'y', 'z'].forEach(axis => {
            const coordDiv = document.createElement('div');
            coordDiv.className = 'ee-coord';
            coordDiv.innerHTML = `
                <div class="ee-coord-label">${axis.toUpperCase()}</div>
                <div class="ee-coord-value" id="ee-${axis}-${chainDef.id}">0.000</div>
            `;
            eeDiv.appendChild(coordDiv);
        });
        
        container.appendChild(eeDiv);
        
        // Target position inputs
        const targetDiv = document.createElement('div');
        targetDiv.className = 'target-inputs';
        
        ['x', 'y', 'z'].forEach(axis => {
            const inputDiv = document.createElement('div');
            inputDiv.className = 'target-input';
            
            const label = document.createElement('label');
            label.textContent = `Target ${axis.toUpperCase()}:`;
            label.htmlFor = `target-${axis}-${chainDef.id}`;
            
            const input = document.createElement('input');
            input.type = 'number';
            input.id = `target-${axis}-${chainDef.id}`;
            input.step = '0.001';
            input.value = '0.000';
            
            inputDiv.appendChild(label);
            inputDiv.appendChild(input);
            targetDiv.appendChild(inputDiv);
        });
        
        container.appendChild(targetDiv);
        
        // Ragdoll Mode Toggle
        const ragdollDiv = document.createElement('div');
        ragdollDiv.style.cssText = 'margin: 10px 0; padding: 10px; background: var(--bg-tertiary); border-radius: 4px;';
        
        const ragdollLabel = document.createElement('label');
        ragdollLabel.style.cssText = 'display: flex; align-items: center; gap: 8px; cursor: pointer;';
        
        const ragdollCheck = document.createElement('input');
        ragdollCheck.type = 'checkbox';
        ragdollCheck.id = `ragdoll-${chainDef.id}`;
        ragdollCheck.addEventListener('change', (e) => {
            this.onRagdollModeToggle(chainDef.id, e.target.checked);
        });
        
        const ragdollText = document.createElement('span');
        ragdollText.textContent = 'Ragdoll Mode (Drag End-Effector)';
        ragdollText.style.fontWeight = '500';
        
        ragdollLabel.appendChild(ragdollCheck);
        ragdollLabel.appendChild(ragdollText);
        ragdollDiv.appendChild(ragdollLabel);
        
        const ragdollHelp = document.createElement('div');
        ragdollHelp.style.cssText = 'font-size: 11px; color: var(--text-muted); margin-top: 4px;';
        ragdollHelp.textContent = 'Enable to interactively move end-effector in 3D view. Press G (translate) or R (rotate).';
        ragdollDiv.appendChild(ragdollHelp);
        
        container.appendChild(ragdollDiv);
        
        // IK buttons
        const buttonsDiv = document.createElement('div');
        buttonsDiv.className = 'ik-buttons';
        
        const solveBtn = document.createElement('button');
        solveBtn.className = 'solve-ik-btn';
        solveBtn.textContent = 'Solve IK';
        solveBtn.addEventListener('click', () => {
            this.onSolveIK(chainDef.id);
        });
        
        const syncBtn = document.createElement('button');
        syncBtn.className = 'sync-ee-btn';
        syncBtn.textContent = 'Sync from Joints';
        syncBtn.addEventListener('click', () => {
            this.onSyncEE(chainDef.id);
        });
        
        buttonsDiv.appendChild(solveBtn);
        buttonsDiv.appendChild(syncBtn);
        container.appendChild(buttonsDiv);
        
        return container;
    }

    /**
     * Show task space panel for a specific chain
     * @param {string} chainId 
     */
    showTaskSpace(chainId) {
        const panel = document.getElementById(`task-space-${chainId}`);
        if (panel) {
            panel.style.display = 'block';
            this.updateTaskSpaceDisplay(chainId);
        }
    }

    /**
     * Hide task space panel for a specific chain
     * @param {string} chainId 
     */
    hideTaskSpace(chainId) {
        const panel = document.getElementById(`task-space-${chainId}`);
        if (panel) {
            panel.style.display = 'none';
        }
    }

    /**
     * Update task space display for a chain
     * @param {string} chainId 
     */
    updateTaskSpaceDisplay(chainId) {
        const chain = this.chainManager.getChain(chainId);
        if (!chain) return;
        
        const eePos = chain.getEndEffectorPosition();
        
        ['x', 'y', 'z'].forEach(axis => {
            const elem = document.getElementById(`ee-${axis}-${chainId}`);
            if (elem) {
                elem.textContent = eePos[axis].toFixed(4);
            }
        });
    }

    /**
     * Handle solve IK button click
     * @param {string} chainId 
     */
    async onSolveIK(chainId) {
        const chain = this.chainManager.getChain(chainId);
        if (!chain) return;
        
        // Get target position from inputs
        const target = {
            x: parseFloat(document.getElementById(`target-x-${chainId}`).value),
            y: parseFloat(document.getElementById(`target-y-${chainId}`).value),
            z: parseFloat(document.getElementById(`target-z-${chainId}`).value)
        };
        
        // Get current joint angles as initial guess
        const initialGuess = chain.getJointAngles();
        
        // Call IK solver
        const chainDef = this.currentRobot.chains.find(c => c.id === chainId);
        const solution = computeIK(chainDef, target, initialGuess);
        
        if (solution) {
            // Apply solution to chain and update UI
            chain.setAllJointAngles(solution);
            
            // Update sliders and number inputs
            solution.forEach((angle, index) => {
                const slider = document.getElementById(`slider-${chainId}-${index}`);
                const numberInput = document.getElementById(`number-${chainId}-${index}`);
                
                if (slider && numberInput) {
                    // Slider shows total angle (offset + variable)
                    const joint = chain.joints[index];
                    const displayAngle = joint.virtual ? angle : (joint.theta + angle);
                    const degrees = radToDeg(displayAngle);
                    slider.value = degrees;
                    numberInput.value = degrees.toFixed(0);
                }
            });
            
            this.updateTaskSpaceDisplay(chainId);
            
            alert(`IK solution found for ${chainDef.name}!`);
        } else {
            alert(`No IK solution found for ${chainDef.name}. The IK solver is not yet implemented.`);
        }
    }

    /**
     * Handle sync from joints button click
     * @param {string} chainId 
     */
    onSyncEE(chainId) {
        const chain = this.chainManager.getChain(chainId);
        if (!chain) return;
        
        // Get current EE position
        const eePos = chain.getEndEffectorPosition();
        
        // Update target inputs
        ['x', 'y', 'z'].forEach(axis => {
            const input = document.getElementById(`target-${axis}-${chainId}`);
            if (input) {
                input.value = eePos[axis].toFixed(4);
            }
        });
        
        this.updateTaskSpaceDisplay(chainId);
    }

    /**
     * Show all chains
     */
    showAllChains() {
        if (!this.currentRobot) return;
        
        this.currentRobot.chains.forEach(chainDef => {
            const checkbox = document.getElementById(`chain-${chainDef.id}`);
            if (checkbox && !checkbox.checked) {
                checkbox.checked = true;
                this.onChainToggle(chainDef.id, true);
            }
        });
    }

    /**
     * Hide all chains
     */
    hideAllChains() {
        if (!this.currentRobot) return;
        
        this.currentRobot.chains.forEach(chainDef => {
            const checkbox = document.getElementById(`chain-${chainDef.id}`);
            if (checkbox && checkbox.checked) {
                checkbox.checked = false;
                this.onChainToggle(chainDef.id, false);
            }
        });
    }
    
    /**
     * Add a new joint to a chain
     * @param {string} chainId 
     * @param {boolean} isVirtual - whether to add a virtual joint
     */
    addJointToChain(chainId, isVirtual = false, insertIndex = -1) {
        console.log(`Adding joint to chain: ${chainId}, isVirtual: ${isVirtual}, insertIndex: ${insertIndex}`);
        const chain = this.chainManager.getChain(chainId);
        if (!chain) {
            console.error(`Chain ${chainId} not found`);
            return;
        }
        
        // Add a default joint
        const newJoint = {
            theta: 0,
            d: isVirtual ? 0 : 0,
            a: isVirtual ? 0 : 0.05,
            alpha: 0,
            visible: true,
            virtual: isVirtual,
            joint_type: isVirtual ? 'fixed' : 'revolute',
            limits: { lower: -3.14, upper: 3.14, effort: 100, velocity: 1.0 }
        };
        
        // Insert at position or append at end
        const idx = (insertIndex >= 0 && insertIndex <= chain.joints.length) ? insertIndex : chain.joints.length;
        chain.joints.splice(idx, 0, newJoint);
        chain.jointAngles.splice(idx, 0, 0);
        console.log(`Joint inserted at index ${idx}, chain now has ${chain.joints.length} joints`);
        
        chain.updateFK();
        
        // Force rebuild visualization to include new joint
        chain.clearVisualization();
        chain.updateVisualization();
        console.log('Visualization updated');
        
        // Ensure chain is active and visible
        if (!this.activeChains.has(chainId)) {
            console.log('Chain was inactive, activating...');
            this.activeChains.add(chainId);
            chain.show();
            this.showDHTable(chainId);
            this.showTaskSpace(chainId);
            
            // Update checkbox
            const checkbox = document.getElementById(`chain-${chainId}`);
            if (checkbox) {
                checkbox.checked = true;
            }
        }
        
        // Update the table (rebuild entirely since indices shift)
        const tbody = document.getElementById(`tbody-${chainId}`);
        console.log(`Looking for tbody-${chainId}:`, tbody);
        if (tbody) {
            tbody.innerHTML = '';
            chain.joints.forEach((joint, i) => {
                const row = this.createJointTableRow(chainId, i, joint);
                tbody.appendChild(row);
            });
            console.log(`Table rebuilt, tbody now has ${tbody.children.length} rows`);
            
            // Update Python code after adding joint
            this.updatePythonCodeDisplay(chainId);
        } else {
            console.error(`tbody-${chainId} not found! Table might not be visible.`);
            // Try to find the table container
            const tableContainer = document.getElementById(`dh-table-${chainId}`);
            console.log(`Table container dh-table-${chainId}:`, tableContainer);
            if (tableContainer) {
                console.log(`Table display style: ${tableContainer.style.display}`);
            }
        }
        
        // Update robot definition
        const chainDef = this.currentRobot.chains.find(c => c.id === chainId);
        if (chainDef) {
            chainDef.joints.splice(idx, 0, newJoint);
            console.log(`Robot definition updated, chain has ${chainDef.joints.length} joints`);
        }
        
        this.updateTaskSpaceDisplay(chainId);
    }
    
    /**
     * Delete a joint from a chain
     * @param {string} chainId 
     * @param {number} index 
     */
    deleteJoint(chainId, index) {
        const chain = this.chainManager.getChain(chainId);
        if (!chain || chain.joints.length <= 1) {
            alert('Cannot delete the last joint!');
            return;
        }
        
        // Remove joint from chain
        chain.joints.splice(index, 1);
        chain.jointAngles.splice(index, 1); // Also remove from jointAngles array
        chain.updateFK();
        
        // Force rebuild visualization
        chain.clearVisualization();
        chain.updateVisualization();
        
        // Update robot definition
        const chainDef = this.currentRobot.chains.find(c => c.id === chainId);
        if (chainDef) {
            chainDef.joints.splice(index, 1);
        }
        
        // Rebuild the table
        const tbody = document.getElementById(`tbody-${chainId}`);
        if (tbody) {
            tbody.innerHTML = '';
            chain.joints.forEach((joint, i) => {
                const row = this.createJointTableRow(chainId, i, joint);
                tbody.appendChild(row);
            });
        }
        
        this.updateTaskSpaceDisplay(chainId);
        this.updatePythonCodeDisplay(chainId);
    }
    
    /**
     * Handle ragdoll mode toggle
     * @param {string} chainId 
     * @param {boolean} enabled 
     */
    onRagdollModeToggle(chainId, enabled) {
        const chain = this.chainManager.getChain(chainId);
        if (!chain) return;
        
        if (enabled) {
            // Disable ragdoll mode for all other chains
            this.currentRobot.chains.forEach(chainDef => {
                if (chainDef.id !== chainId) {
                    const otherChain = this.chainManager.getChain(chainDef.id);
                    if (otherChain && otherChain.ragdollMode) {
                        otherChain.disableRagdollMode();
                        const checkbox = document.getElementById(`ragdoll-${chainDef.id}`);
                        if (checkbox) checkbox.checked = false;
                    }
                }
            });
            
            // Enable for this chain
            chain.enableRagdollMode((targetPos, targetRot) => {
                // IK callback - this will be called when user drags the end-effector
                this.onRagdollIK(chainId, targetPos, targetRot);
            });
        } else {
            chain.disableRagdollMode();
        }
    }
    
    /**
     * Handle IK solving during ragdoll manipulation
     * @param {string} chainId 
     * @param {Object} targetPos - {x, y, z}
     * @param {Object} targetRot - THREE.Quaternion or null
     */
    onRagdollIK(chainId, targetPos, targetRot) {
        const chain = this.chainManager.getChain(chainId);
        if (!chain) return;
        
        // Update target input fields
        ['x', 'y', 'z'].forEach(axis => {
            const input = document.getElementById(`target-${axis}-${chainId}`);
            if (input) {
                input.value = targetPos[axis].toFixed(4);
            }
        });
        
        // Get current joint angles as initial guess
        const initialGuess = chain.getJointAngles();
        
        // Call IK solver
        const chainDef = this.currentRobot.chains.find(c => c.id === chainId);
        const solution = computeIK(chainDef, targetPos, initialGuess);
        
        if (solution) {
            // Apply solution to chain
            chain.setAllJointAngles(solution);
            
            // Update sliders and number inputs
            solution.forEach((angle, index) => {
                if (chain.joints[index].virtual) return; // Skip virtual joints
                
                const slider = document.getElementById(`slider-${chainId}-${index}`);
                const numberInput = document.getElementById(`number-${chainId}-${index}`);
                
                if (slider && numberInput) {
                    // Slider shows total angle (offset + variable)
                    const displayAngle = chain.joints[index].theta + angle;
                    const degrees = radToDeg(displayAngle);
                    slider.value = degrees;
                    numberInput.value = degrees.toFixed(0);
                }
            });
            
            this.updateTaskSpaceDisplay(chainId);
        }
    }
    
    /**
     * Handle DH parameter change
     * @param {string} chainId 
     * @param {number} index 
     * @param {string} param - 'd', 'a', or 'alpha'
     * @param {number} value 
     */
    onDHParamChange(chainId, index, param, value) {
        const chain = this.chainManager.getChain(chainId);
        if (!chain) return;
        
        // Update the parameter (convert alpha from degrees to radians)
        if (param === 'alpha') {
            chain.joints[index].alpha = degToRad(value);
        } else {
            chain.joints[index][param] = value;
        }
        
        // Update robot definition
        const chainDef = this.currentRobot.chains.find(c => c.id === chainId);
        if (chainDef) {
            if (param === 'alpha') {
                chainDef.joints[index].alpha = degToRad(value);
            } else {
                chainDef.joints[index][param] = value;
            }
        }
        
        // Recompute and update visualization
        chain.updateFK();
        chain.updateVisualization();
        this.updateTaskSpaceDisplay(chainId);
        this.updatePythonCodeDisplay(chainId);
    }

    /**
     * Switch export mode between numeric and SymPy
     * @param {string} chainId 
     * @param {string} mode 'numeric' or 'sympy'
     */
    switchPythonMode(chainId, mode) {
        this.pythonExportMode.set(chainId, mode);
        
        // Update button styles
        const numericBtn = document.getElementById(`mode-numeric-${chainId}`);
        const sympyBtn = document.getElementById(`mode-sympy-${chainId}`);
        
        if (mode === 'numeric') {
            numericBtn.style.background = 'var(--accent)';
            numericBtn.style.color = 'white';
            numericBtn.style.fontWeight = '500';
            sympyBtn.style.background = 'rgba(255, 255, 255, 0.1)';
            sympyBtn.style.color = '#aaa';
            sympyBtn.style.fontWeight = 'normal';
        } else {
            numericBtn.style.background = 'rgba(255, 255, 255, 0.1)';
            numericBtn.style.color = '#aaa';
            numericBtn.style.fontWeight = 'normal';
            sympyBtn.style.background = 'var(--accent)';
            sympyBtn.style.color = 'white';
            sympyBtn.style.fontWeight = '500';
        }
        
        this.updatePythonCodeDisplay(chainId);
    }

    /**
     * Display the appropriate Python code (numeric or SymPy) based on current mode
     * @param {string} chainId 
     */
    updatePythonCodeDisplay(chainId) {
        const mode = this.pythonExportMode.get(chainId) || 'numeric';
        if (mode === 'sympy') {
            this.updatePythonCodeSymPy(chainId);
        } else {
            this.updatePythonCode(chainId);
        }
    }

    /**
     * Update Python code display for a chain (numeric version)
     * Generates code compatible with core.dtypes.DHparam / ChainParams
     * @param {string} chainId 
     */
    updatePythonCode(chainId) {
        const chainDef = this.currentRobot.chains.find(c => c.id === chainId);
        if (!chainDef) return;
        
        const codeBlock = document.getElementById(`python-code-${chainId}`);
        if (!codeBlock) return;
        
        const allJoints = chainDef.joints;
        
        // Identify actuated joints (non-virtual, non-fixed)
        const actuatedJoints = allJoints.filter(j => !j.virtual && j.joint_type !== 'fixed');
        const numActuated = actuatedJoints.length;
        
        const lines = [];
        const funcName = `${chainId}_chain`;
        
        // Imports
        lines.push('from core.dtypes import DHparam, ChainParams');
        lines.push('');
        lines.push('');
        
        // Function signature with theta_offsets tuple
        const defaultOffsets = Array(numActuated).fill('0.0').join(', ');
        lines.push(`def ${funcName}(theta_offsets=(${defaultOffsets},)) -> ChainParams:`);
        lines.push(`    """Define the ${chainDef.name || chainId} chain parameters."""`);
        
        // Unpack offsets
        if (numActuated > 0) {
            const offsetNames = Array.from({ length: numActuated }, (_, i) => `o${i + 1}`);
            lines.push(`    ${offsetNames.join(', ')} = theta_offsets`);
            lines.push(`    theta = [${offsetNames.join(', ')}]`);
        }
        
        lines.push('    dh_params = [');
        
        let actuatedIdx = 0;
        
        if (allJoints.length === 0) {
            lines.push('        # No joints in this chain');
        } else {
            allJoints.forEach((joint, idx) => {
                const isLast = idx === allJoints.length - 1;
                const isVirtual = joint.virtual;
                const jointType = joint.joint_type || 'revolute';
                const isPrismatic = joint.isPrismatic || jointType === 'prismatic';
                
                let type;
                if (isVirtual) {
                    type = 'fixed';
                } else {
                    type = isPrismatic ? 'prismatic' : 'revolute';
                }
                
                // theta_offset: for actuated revolute => theta[i], for fixed => numeric value
                let thetaStr;
                if (!isVirtual && type === 'revolute') {
                    thetaStr = `theta[${actuatedIdx}]`;
                    actuatedIdx++;
                } else if (!isVirtual && type === 'prismatic') {
                    thetaStr = joint.theta.toFixed(6);
                    actuatedIdx++;
                } else {
                    thetaStr = joint.theta.toFixed(6);
                }
                
                const comment = isVirtual ? '  # Virtual joint for frame alignment' : '';
                
                lines.push(`        DHparam(a=${joint.a.toFixed(6)}, alpha=${joint.alpha.toFixed(6)}, d=${joint.d.toFixed(6)}, theta_offset=${thetaStr}, joint_type='${type}')${isLast ? '' : ','}${comment}`);
            });
        }
        
        lines.push('    ]');
        lines.push('    return ChainParams(dh_params=dh_params)');
        
        codeBlock.textContent = lines.join('\n');
    }

    /**
     * Update Python code display for a chain (SymPy symbolic version)
     * Generates code compatible with core.dtypes.DHparam / ChainParams using sympy symbols
     * @param {string} chainId 
     */
    updatePythonCodeSymPy(chainId) {
        const chainDef = this.currentRobot.chains.find(c => c.id === chainId);
        if (!chainDef) return;
        
        const codeBlock = document.getElementById(`python-code-${chainId}`);
        if (!codeBlock) return;
        
        const allJoints = chainDef.joints;
        
        // Identify actuated joints (non-virtual, non-fixed)
        const actuatedJoints = allJoints.filter(j => !j.virtual && j.joint_type !== 'fixed');
        const numActuated = actuatedJoints.length;
        
        // Generate symbol names
        const symbolNames = Array.from({ length: numActuated }, (_, i) => `theta_${i + 1}`);
        
        const lines = [];
        const funcName = `${chainId}_chain_symbolic`;
        
        // Imports
        lines.push('from sympy import symbols');
        lines.push('from core.dtypes import DHparam, ChainParams');
        lines.push('');
        lines.push('');
        
        lines.push(`def ${funcName}() -> ChainParams:`);
        lines.push(`    """Define the ${chainDef.name || chainId} chain parameters (SymPy symbolic)."""`);
        
        // Define symbolic variables for actuated joints
        if (numActuated > 0) {
            lines.push(`    ${symbolNames.join(', ')} = symbols('${symbolNames.join(' ')}', real=True)`);
        }
        
        lines.push('    dh_params = [');
        
        let actuatedIdx = 0;
        
        if (allJoints.length === 0) {
            lines.push('        # No joints in this chain');
        } else {
            allJoints.forEach((joint, idx) => {
                const isLast = idx === allJoints.length - 1;
                const isVirtual = joint.virtual;
                const jointType = joint.joint_type || 'revolute';
                const isPrismatic = joint.isPrismatic || jointType === 'prismatic';
                
                let type;
                if (isVirtual) {
                    type = 'fixed';
                } else {
                    type = isPrismatic ? 'prismatic' : 'revolute';
                }
                
                // theta_offset: for actuated revolute => symbolic theta_i, for fixed => numeric
                let thetaStr;
                if (!isVirtual && type === 'revolute') {
                    thetaStr = symbolNames[actuatedIdx];
                    actuatedIdx++;
                } else if (!isVirtual && type === 'prismatic') {
                    thetaStr = joint.theta.toFixed(6);
                    actuatedIdx++;
                } else {
                    thetaStr = joint.theta.toFixed(6);
                }
                
                const comment = isVirtual ? '  # Virtual joint for frame alignment' : '';
                
                lines.push(`        DHparam(a=${joint.a.toFixed(6)}, alpha=${joint.alpha.toFixed(6)}, d=${joint.d.toFixed(6)}, theta_offset=${thetaStr}, joint_type='${type}')${isLast ? '' : ','}${comment}`);
            });
        }
        
        lines.push('    ]');
        lines.push('    return ChainParams(dh_params=dh_params)');
        
        codeBlock.textContent = lines.join('\n');
    }

    /**
     * Copy chain Python code to clipboard
     * @param {string} chainId 
     */
    copyChainToPython(chainId) {
        const codeBlock = document.getElementById(`python-code-${chainId}`);
        if (!codeBlock) {
            alert('Code block not found!');
            return;
        }
        
        // If code block is empty, generate the code
        if (!codeBlock.textContent || codeBlock.textContent.trim().length === 0) {
            this.updatePythonCodeDisplay(chainId);
        }
        
        const code = codeBlock.textContent;
        const chainDef = this.currentRobot.chains.find(c => c.id === chainId);
        
        if (!code || code.trim().length === 0) {
            alert('No code to copy. Code block is empty.');
            return;
        }
        
        navigator.clipboard.writeText(code).then(() => {
            alert(`✓ Python function for ${chainDef.name} copied to clipboard!`);
        }).catch(err => {
            console.error('Failed to copy:', err);
            alert('Copy failed. Code:\n\n' + code);
        });
    }
}
