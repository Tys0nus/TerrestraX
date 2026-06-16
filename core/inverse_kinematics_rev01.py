from dataclasses import field
from typing import Tuple

import numpy as np
from sympy import Matrix, lambdify, symbols

from core.dtypes import ChainParams, IKParams, IKinfo, JointVec, Vec3
from core.kinematics import chain_footpoint, chain_jacobian

inverse_kinematics: Matrix = field(init=False, repr=False)


class LegIK:
    def __init__(self, chain: ChainParams, T0: Matrix = Matrix.eye(4)):
        self.chain = chain
        self.T0 = T0

        q_count = len([link for link in chain.dh_params if link.joint_type in ["revolute", "prismatic"]])
        q_syms = Matrix(symbols(f"q0:{q_count}"))
        self.q_syms = q_syms

        p_syms = chain_footpoint(self.chain, q_syms, self.T0)
        J_syms = chain_jacobian(self.chain, q_syms, self.T0)

        fk_fn = lambdify(q_syms, p_syms, "numpy")
        jac_fn = lambdify(q_syms, J_syms, "numpy")

        def fk_np(q: JointVec) -> Vec3:
            q = np.asarray(q, np.float64).flatten()
            p = np.array(fk_fn(*q), dtype=np.float64).reshape(3,)
            return p

        def jac_np(q: JointVec) -> np.ndarray:
            q = np.asarray(q, np.float64).flatten()
            J = np.array(jac_fn(*q), dtype=np.float64).reshape(3, len(q))
            return J

        self.fk_np = fk_np
        self.jac_np = jac_np

    def ik_step(self, q: JointVec, target: Vec3) -> Tuple[JointVec, Vec3]:
        """
        Single resolved-rate IK step:
        dq = pinv(J) @ (target - current_position)
        """
        q = np.asarray(q, np.float64).flatten()
        target = np.asarray(target, np.float64).flatten()

        current_pos = self.fk_np(q)
        error = target - current_pos
        J = self.jac_np(q)
        dq = np.linalg.pinv(J) @ error
        return dq, error

    def step_solve(self, q: JointVec, target: Vec3, params: IKParams) -> Tuple[JointVec, IKinfo]:
        """Perform one bounded IK step towards the target."""
        q = np.asarray(q, np.float64).flatten()
        dq, error = self.ik_step(q, target)
        dq = np.clip(dq, -params.max_dq, params.max_dq)
        q_target = q + params.alpha * dq
        err_norm = float(np.linalg.norm(error))
        return q_target, IKinfo(ok=err_norm < params.tol, iters=1, err=err_norm)
    
    def solve(self, q_init: JointVec, target: Vec3, params: IKParams) -> Tuple[JointVec, IKinfo]:
        """Iteratively solve IK until convergence or max iterations."""
        q = np.asarray(q_init, np.float64).flatten()
        for i in range(params.max_iters):
            q, info = self.step_solve(q, target, params)
            if info.ok:
                return q, IKinfo(ok=True, iters=i+1, err=info.err)
        return q, IKinfo(ok=False, iters=params.max_iters, err=info.err)