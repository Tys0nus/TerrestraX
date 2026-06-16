from core.trajectory.time_laws import time_law
from core.dtypes import Vec3, JointVec
import math
import numpy as np

def lerp(s: float, p0: Vec3, p1: Vec3) -> Vec3:
    """Linear interpolation between two points."""
    p = (1-s)*p0 + s*p1
    return p

def path_static_sinusoid(s: float, p0: Vec3, A: float, H: float) -> Vec3:
    """Static path with fixed horizontal offset and vertical height."""
    x = p0[0] + A * math.sin(2*math.pi*s)
    y = p0[1]
    z = p0[2] + H * max(0, math.sin(2*math.pi*s))
    return np.array([x, y, z], dtype=float)

# def path_swing

# def path_stance