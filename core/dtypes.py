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
    dh_params: Sequence[DHparam]  # Sequence of DH parameters for each link    

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
