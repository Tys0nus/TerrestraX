# foot movements
from numpy import ndarray
from core.dtypes import ChainPose, ChainParams, JointVec, RobotPose

global phi
phi = 0.0
beta = 0.6

swi = (phi - beta)/(1-beta)

def foot_targets ()
    """Define foot target positions for trajectory planning."""

    return targets