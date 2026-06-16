from dataclasses import dataclass
from typing import Sequence, Literal, Union
from sympy import symbols, Basic

import numpy as np

NpSym = Union[float, int, Basic]

Vec3 = np.ndarray  # 3D vector
JointVec = np.ndarray  # Joint vector

@dataclass
class DHparam:
    """Denavit-Hartenberg parameter representation for robotic arms."""
    a: NpSym  # Link length
    alpha: NpSym  # Link twist
    d: NpSym  # Link offset
    theta_offset: NpSym = 0.0 # Joint angle
    joint_type: Literal['revolute', 'prismatic', 'fixed'] = 'revolute'  # Joint type
    isvirtual: bool = False 

@dataclass
class ChainParams:
    """Skeletal arm representation using DH parameters."""
    dh_params: Sequence[DHparam]  # Sequence of DH paramrs for each link    

@dataclass(frozen=True)
class IKinfo:
    ok: bool
    iters: int
    err: float

@dataclass(frozen=True)
class IKParams:
    """Parameters for inverse kinematics solver."""
    alpha: float = 0.1  # Step size for gradient descent
    max_dq: float = 0.25  # Maximum change in joint angles per iteration
    max_iters: int = 30  # Maximum iterations for convergence
    tol: float = 1e-4  # Tolerance for convergence

@dataclass(frozen=True)
class ChainPose:
    """Pose of a robotic chain."""
    coxa:float
    femur:float
    tibia:float

@dataclass(frozen=True)
class RobotPose:
    """Pose of the robot with four legs."""
    FL: ChainPose
    FR: ChainPose
    RL: ChainPose
    RR: ChainPose


### Leg trajectory types

@dataclass(frozen=True)
class Limits:
    """Joint limits and velocity/acceleration constraints."""
    v_max: np.ndarray  # Maximum vel
    a_max: np.ndarray  # Maximum acc
    jerk_max: np.ndarray  # Maximum jerk
