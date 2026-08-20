// urdf-utils.js
// URDF export/import utilities for robot definition interoperability

import { radToDeg, degToRad } from './math.js';

/**
 * Convert robot definition to URDF XML format
 * @param {Object} robot - Robot definition with chains
 * @returns {string} URDF XML string
 */
export function exportToURDF(robot) {
    const lines = [];
    lines.push('<?xml version="1.0"?>');
    lines.push(`<robot name="${robot.name || 'robot'}">`);
    lines.push('');
    
    // Add a base link
    lines.push('  <link name="base_link">');
    lines.push('    <visual>');
    lines.push('      <geometry>');
    lines.push('        <box size="0.05 0.05 0.05"/>');
    lines.push('      </geometry>');
    lines.push('      <material name="grey">');
    lines.push('        <color rgba="0.5 0.5 0.5 1"/>');
    lines.push('      </material>');
    lines.push('    </visual>');
    lines.push('  </link>');
    lines.push('');
    
    robot.chains.forEach((chain, chainIdx) => {
        const chainName = chain.id || `chain_${chainIdx}`;
        let parentLink = 'base_link';
        
        // Base transform joint if needed
        const basePos = chain.baseTransform || [0, 0, 0];
        if (basePos[0] !== 0 || basePos[1] !== 0 || basePos[2] !== 0) {
            const baseJointName = `${chainName}_base_joint`;
            const baseLinkName = `${chainName}_base_link`;
            
            lines.push(`  <joint name="${baseJointName}" type="fixed">`);
            lines.push(`    <parent link="${parentLink}"/>`);
            lines.push(`    <child link="${baseLinkName}"/>`);
            lines.push(`    <origin xyz="${basePos[0]} ${basePos[1]} ${basePos[2]}" rpy="0 0 0"/>`);
            lines.push('  </joint>');
            lines.push('');
            
            lines.push(`  <link name="${baseLinkName}">`);
            lines.push('    <visual>');
            lines.push('      <geometry>');
            lines.push('        <sphere radius="0.01"/>');
            lines.push('      </geometry>');
            lines.push('    </visual>');
            lines.push('  </link>');
            lines.push('');
            
            parentLink = baseLinkName;
        }
        
        // Convert each joint in the DH chain
        chain.joints.forEach((joint, jointIdx) => {
            const jointName = `${chainName}_joint_${jointIdx + 1}`;
            const linkName = `${chainName}_link_${jointIdx + 1}`;
            const jointType = joint.joint_type || 'revolute';
            const isVirtual = joint.virtual || false;
            
            // Convert DH parameters to URDF origin (xyz, rpy)
            // Standard DH: T = Rz(theta) * Tz(d) * Tx(a) * Rx(alpha)
            const xyz = `${joint.a} 0 ${joint.d}`;
            const rpy = `${joint.alpha} 0 0`; // Note: theta is the joint variable
            
            lines.push(`  <joint name="${jointName}" type="${isVirtual ? 'fixed' : jointType}">`);
            lines.push(`    <parent link="${parentLink}"/>`);
            lines.push(`    <child link="${linkName}"/>`);
            lines.push(`    <origin xyz="${xyz}" rpy="${rpy}"/>`);
            
            if (!isVirtual && jointType === 'revolute') {
                lines.push('    <axis xyz="0 0 1"/>');
                const limits = joint.limits || { lower: -3.14, upper: 3.14, effort: 100, velocity: 1.0 };
                lines.push(`    <limit lower="${limits.lower}" upper="${limits.upper}" effort="${limits.effort}" velocity="${limits.velocity}"/>`);
            } else if (!isVirtual && jointType === 'prismatic') {
                lines.push('    <axis xyz="0 0 1"/>');
                const limits = joint.limits || { lower: -0.5, upper: 0.5, effort: 100, velocity: 1.0 };
                lines.push(`    <limit lower="${limits.lower}" upper="${limits.upper}" effort="${limits.effort}" velocity="${limits.velocity}"/>`);
            }
            
            lines.push('  </joint>');
            lines.push('');
            
            // Add link
            lines.push(`  <link name="${linkName}">`);
            lines.push('    <visual>');
            lines.push('      <geometry>');
            if (joint.a > 0) {
                lines.push(`        <cylinder radius="0.01" length="${joint.a}"/>`);
                lines.push(`      </geometry>`);
                lines.push(`      <origin xyz="${joint.a / 2} 0 0" rpy="0 1.57079632679 0"/>`);
            } else {
                lines.push('        <sphere radius="0.015"/>');
                lines.push('      </geometry>');
            }
            lines.push('      <material name="blue">');
            lines.push('        <color rgba="0.2 0.4 0.8 1"/>');
            lines.push('      </material>');
            lines.push('    </visual>');
            lines.push('  </link>');
            lines.push('');
            
            parentLink = linkName;
        });
        
        // Add end-effector link
        const eeName = `${chainName}_ee`;
        lines.push(`  <joint name="${chainName}_ee_joint" type="fixed">`);
        lines.push(`    <parent link="${parentLink}"/>`);
        lines.push(`    <child link="${eeName}"/>`);
        lines.push('    <origin xyz="0 0 0" rpy="0 0 0"/>');
        lines.push('  </joint>');
        lines.push('');
        
        lines.push(`  <link name="${eeName}">`);
        lines.push('    <visual>');
        lines.push('      <geometry>');
        lines.push('        <sphere radius="0.02"/>');
        lines.push('      </geometry>');
        lines.push('      <material name="red">');
        lines.push('        <color rgba="1 0 0 1"/>');
        lines.push('      </material>');
        lines.push('    </visual>');
        lines.push('  </link>');
        lines.push('');
    });
    
    lines.push('</robot>');
    
    return lines.join('\n');
}

/**
 * Generate ROS launch file for RViz visualization
 * @param {string} robotName 
 * @returns {string} Launch file XML
 */
export function generateRVizLaunch(robotName) {
    return `<?xml version="1.0"?>
<launch>
  <arg name="model" default="$(find ${robotName}_description)/urdf/${robotName}.urdf"/>
  <arg name="rvizconfig" default="$(find ${robotName}_description)/rviz/${robotName}.rviz"/>
  
  <param name="robot_description" command="$(find xacro)/xacro $(arg model)"/>
  
  <node name="joint_state_publisher_gui" pkg="joint_state_publisher_gui" type="joint_state_publisher_gui"/>
  <node name="robot_state_publisher" pkg="robot_state_publisher" type="robot_state_publisher"/>
  <node name="rviz" pkg="rviz" type="rviz" args="-d $(arg rvizconfig)" required="true"/>
</launch>`;
}

/**
 * Generate MoveIt configuration package structure info
 * @param {string} robotName 
 * @returns {Object} Configuration file templates
 */
export function generateMoveItConfig(robotName) {
    return {
        packageXml: `<?xml version="1.0"?>
<package format="2">
  <name>${robotName}_moveit_config</name>
  <version>0.1.0</version>
  <description>MoveIt configuration for ${robotName}</description>
  
  <maintainer email="user@todo.todo">User</maintainer>
  <license>BSD</license>
  
  <buildtool_depend>catkin</buildtool_depend>
  
  <exec_depend>moveit_ros_move_group</exec_depend>
  <exec_depend>moveit_planners_ompl</exec_depend>
  <exec_depend>moveit_ros_visualization</exec_depend>
  <exec_depend>joint_state_publisher</exec_depend>
  <exec_depend>robot_state_publisher</exec_depend>
  <exec_depend>xacro</exec_depend>
</package>`,
        
        readme: `# ${robotName} MoveIt Configuration

This package contains MoveIt configuration files for the ${robotName} robot.

## Installation

1. Copy this package to your catkin workspace: \`catkin_ws/src/\`
2. Build the workspace: \`catkin_make\`
3. Source the workspace: \`source devel/setup.bash\`

## Usage

Launch MoveIt with RViz:
\`\`\`bash
roslaunch ${robotName}_moveit_config demo.launch
\`\`\`

## Files Generated from DH Visualizer

- URDF file with joint definitions from DH parameters
- Virtual joints marked as 'fixed' type
- Joint limits and effort values included
- Ready for Gazebo simulation and real robot deployment
`
    };
}

/**
 * Download text content as file
 * @param {string} filename 
 * @param {string} content 
 */
export function downloadFile(filename, content) {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
