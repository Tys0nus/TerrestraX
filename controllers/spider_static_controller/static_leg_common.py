from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sympy import Matrix

from core.dtypes import IKParams
from core.inverse_kinematics import LegIK
from core.trajectory import time_laws
from core.trajectory.paths import path_static
from robots.rconfig import FL_chain


@dataclass
class StaticLegControllerConfig:
    cycle_s: float = 2.5
    amplitude_m: float = 0.035
    lift_height_m: float = 0.020
    solver_steps: int = 3
    ik_params: IKParams = field(default_factory=lambda: IKParams(alpha=0.55, max_dq=0.25, tol=1e-4))


class StaticLegController:
    def __init__(self, config: StaticLegControllerConfig | None = None):
        self.config = config or StaticLegControllerConfig()

        chain = FL_chain()
        t0_base = Matrix(
            [
                [1, 0, 0, 0.060000],
                [0, 1, 0, 0.060000],
                [0, 0, 1, 0.094700],
                [0, 0, 0, 1],
            ]
        )
        self.ik = LegIK(chain, t0_base)

        self.q = np.zeros(3, dtype=float)
        self.p0 = self.ik.fk_np(self.q)
        self.t = 0.0

    def step(self, dt_s: float) -> np.ndarray:
        self.t += float(dt_s)

        s = time_laws.time_law_static(self.t, self.config.cycle_s)
        p_des = path_static(s, self.p0, self.config.amplitude_m, self.config.lift_height_m)

        for _ in range(self.config.solver_steps):
            self.q, _ = self.ik.step_solve(self.q, p_des, self.config.ik_params)

        return self.q.copy()

    def snapshot(self) -> dict[str, float]:
        return {
            "t": float(self.t),
            "q0": float(self.q[0]),
            "q1": float(self.q[1]),
            "q2": float(self.q[2]),
        }
