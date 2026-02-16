def FL_chain_symbolic() -> dict:
    """Define the Front Left Leg chain parameters for symbolic computation (SymPy)."""
    from core.dtypes import DHparam, ChainParams, JointVec
    from sympy import symbols, cos, sin, pi, Matrix, simplify
    
from core.dtypes import DHparam, ChainParams
from sympy import symbols
import numpy as np

    def FL_chain() -> ChainParams:
        """Define the Front Left Leg chain parameters."""

        theta_1, theta_2, theta_3 = symbols('theta_1 theta_2 theta_3', real=True)
        dh_params = [
            {'a': 0.084853, 'alpha': 0.000000, 'd': 0.000000, 'theta': 0.785398, 'type': 'fixed'},  # Virtual joint for frame alignment
            {'a': 0.000000, 'alpha': 0.000000, 'd': 0.000000, 'theta': theta_1 + 0.000000, 'type': 'revolute'},
            {'a': 0.040000, 'alpha': 1.570796, 'd': 0.000000, 'theta': 0.000000, 'type': 'fixed'},  # Virtual joint for frame alignment
            {'a': 0.000000, 'alpha': 0.000000, 'd': 0.000000, 'theta': -0.785398, 'type': 'fixed'},  # Virtual joint for frame alignment
            {'a': 0.000000, 'alpha': 0.000000, 'd': 0.000000, 'theta': theta_2 + 0.000000, 'type': 'revolute'},
            {'a': 0.035000, 'alpha': 0.000000, 'd': 0.000000, 'theta': 0.000000, 'type': 'fixed'},  # Virtual joint for frame alignment
            {'a': 0.000000, 'alpha': 0.000000, 'd': 0.000000, 'theta': -0.785398, 'type': 'fixed'},  # Virtual joint for frame alignment
            {'a': 0.000000, 'alpha': 0.000000, 'd': 0.000000, 'theta': theta_3 + 0.000000, 'type': 'revolute'},
            {'a': 0.070000, 'alpha': 0.000000, 'd': 0.000000, 'theta': 0.000000, 'type': 'fixed'},  # Virtual joint for frame alignment
            {'a': 0.000000, 'alpha': -1.570796, 'd': 0.000000, 'theta': 1.570796, 'type': 'fixed'},  # Virtual joint for frame alignment
            {'a': 0.000000, 'alpha': 0.000000, 'd': 0.000000, 'theta': -0.785398, 'type': 'fixed'}  # Virtual joint for frame alignment
        ]
        return ChainParams(dh_params=dh_params)
    
    # Function to compute DH transformation matrix (symbolic)
    def dh_transform(a, alpha, d, theta):
        """Generate symbolic DH transformation matrix."""
        c_t = cos(theta)
        s_t = sin(theta)
        c_a = cos(alpha)
        s_a = sin(alpha)
        
        return Matrix([
            [c_t, -s_t*c_a, s_t*s_a, a*c_t],
            [s_t, c_t*c_a, -c_t*s_a, a*s_t],
            [0, s_a, c_a, d],
            [0, 0, 0, 1]
        ])
    
    # Compute forward kinematics (symbolic 4x4 matrices)
    T0_base = Matrix([
        [1, 0, 0, 0.060000],
        [0, 1, 0, 0.060000],
        [0, 0, 1, 0.094700],
        [0, 0, 0, 1]
    ])
    
    T = T0_base
    transforms = [T]
    
    for param in dh_params:
        T_i = dh_transform(param['a'], param['alpha'], param['d'], param['theta'])
        T = simplify(T @ T_i)
        transforms.append(T)
    
    # End-effector transformation matrix
    T_ee = transforms[-1]
    p_ee = T_ee[:3, 3]
    
    # Compute position Jacobian (3 x num_actuated)
    joint_symbols = [theta_1, theta_2, theta_3]
    jacobian_position = Matrix([[p_ee[i].diff(q) for q in joint_symbols] for i in range(3)])
    
    return {
        'dh_params': dh_params,
        'base_position': [0.060000, 0.060000, 0.094700],
        'joint_symbols': joint_symbols,
        'forward_kinematics': T_ee,
        'end_effector_position': p_ee,
        'jacobian_position': jacobian_position,
        'num_actuated_joints': 3
    }