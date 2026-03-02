from dataclasses import dataclass, field
from core.dtypes import DHparam, ChainParams, JointVec, NpSym, Vec3
import numpy as np
from sympy import symbols, Basic, Matrix, cos, sin, simplify

forward_kinematics: Matrix = field(init=False, repr=False)

def dh_transform(link: DHparam, q_i: NpSym) -> Matrix:
    """Compute the Denavit-Hartenberg transformation matrix."""
    
    if link.joint_type == 'revolute':
        theta = link.theta_offset + q_i
        d = link.d
    elif link.joint_type == 'prismatic':
        d = link.d + q_i
        theta = link.theta_offset
    elif link.joint_type == 'fixed':
        theta = link.theta_offset
        d = link.d
    else:
        raise ValueError(f"Unknown joint type: {link.joint_type}")

    a = link.a
    alpha = link.alpha

    c_a = cos(alpha)
    s_a = sin(alpha)
    c_t = cos(theta)
    s_t = sin(theta)

    T = Matrix([
        [c_t, -s_t * c_a,  s_t * s_a, a * c_t],
        [s_t,  c_t * c_a, -c_t * s_a, a * s_t],
        [0,      s_a,      c_a,      d   ],
        [0,      0,       0,      1   ]])

    return T

def chain_kin(chain: ChainParams, q: NpSym) -> Matrix:
    """Compute the forward kinematics for a robotic chain."""
    T = Matrix.eye(4)
    q_finder = 0

    for link in chain.dh_params:
        if link.joint_type in ['revolute','prismatic']:
            qi = q[q_finder]
            q_finder += 1
            T_link = dh_transform(link, qi)
            T = T * T_link
        else:  # fixed joint
            qi = 0.0      
            T_link = dh_transform(link, qi)
            T = T * T_link

    assert q_finder == len(q), "Joint vector length does not match number of movable joints."      
    return T

def chain_footpoint(chain: ChainParams, q: NpSym, T0: Matrix = Matrix.eye(4)) -> Vec3:
    """Compute the end-effector position for a robotic chain."""
    
    T = chain_kin(chain, q)
    T = T0 * T
    return T[0:3, 3]

def chain_jacobian(chain: ChainParams, q: NpSym, T0: Matrix = Matrix.eye(4)) -> Matrix:
    """Compute the Jacobian matrix for a robotic chain."""

    p_ee = chain_footpoint(chain, q, T0)
    J = p_ee.jacobian(q)
    return simplify(J)

