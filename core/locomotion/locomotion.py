import numpy as np
from core.dtypes import Vec3

class Locomotion:
    """
    i/p: vx, vy, omega
    leg phase tracking
    o/p: foot targets for each leg
    """
    def __init__(self, nominal_feet, step_height: float = 0.02, step_freq : float = 2.0, duty_cycle: float = 0.6, T0: np.ndarray = np.eye(4)):
        self.nominal_feet = nominal_feet
        self.step_height = step_height
        self.step_freq = step_freq
        self.duty_cycle = duty_cycle
        self.phase = {leg: 0.0 for leg in LEG_IDS}
        self.T0 = T0

    
    def update(self, vx: float, vy: float, omega: float, dt: float) -> dict[str, Vec3]:
        dphi = self.step_freq * dt 
        foot_targets = {}

