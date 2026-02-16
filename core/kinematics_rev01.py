from dataclasses import dataclass
from core.dtypes import DHparam, ChainParams, JointVec, Vec3
import numpy as np

def dh_transform(link: DHparam, q_i: float) -> np.ndarray:
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

    ca, sa = np.cos(alpha), np.sin(alpha)
    ct, st = np.cos(theta), np.sin(theta)

    return np.array([
        [ct, -st * ca,  st * sa, a * ct],
        [st,  ct * ca, -ct * sa, a * st],
        [0,      sa,      ca,      d   ],
        [0,      0,       0,      1   ]])

def chain_kin(chain: ChainParams, q: JointVec) -> np.ndarray:
    """Compute the forward kinematics for a robotic chain."""
    
    dh_params = chain.dh_params

    T = np.eye(4)  # Initialize transformation matrix as identity

    q_finder = 0

    for link in dh_params:
        if link.joint_type in ['revolute', 'prismatic']:
            qi = q[q_finder]
            q_finder += 1
        else:  # fixed joint
            qi = 0.0

        T_link = dh_transform(link, qi)
        T = T @ T_link

    assert q_finder == len(q), "Joint vector length does not match number of movable joints."

    return T

def chain_footpoint(chain: ChainParams, q: JointVec) -> Vec3:
    """Compute the end-effector position for a robotic chain."""
    
    T = chain_kin(chain, q)
    return T[0:3, 3]

# def chain_jacobian(chain