"""Symbolic kinematics helpers using SymPy.

Keep runtime control loops in NumPy, but use this module to derive/verify
forward kinematics and Jacobians, then lambdify to fast numeric functions.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Sequence

from core.types import ChainParams, DHparam


def _sympy():
    # Lazy import so runtime code doesn't require SymPy.
    import sympy as sp  # type: ignore

    return sp


def make_symbolic_q(chain: ChainParams, prefix: str = "q"):
    """Create a list of symbolic joint variables for movable joints."""
    sp = _sympy()
    n = sum(1 for link in chain.dh_params if link.joint_type in ("revolute", "prismatic"))
    return list(sp.symbols(f"{prefix}0:{n}"))


def dh_transform_sym(link: DHparam, q_i):
    """Symbolic Denavit-Hartenberg transform."""
    sp = _sympy()
    if link.joint_type == "revolute":
        theta = link.theta_offset + q_i
        d = link.d
    elif link.joint_type == "prismatic":
        d = link.d + q_i
        theta = link.theta_offset
    elif link.joint_type == "fixed":
        theta = link.theta_offset
        d = link.d
    else:
        raise ValueError(f"Unknown joint type: {link.joint_type}")

    a = link.a
    alpha = link.alpha

    ca, sa = sp.cos(alpha), sp.sin(alpha)
    ct, st = sp.cos(theta), sp.sin(theta)

    return sp.Matrix(
        [
            [ct, -st * ca, st * sa, a * ct],
            [st, ct * ca, -ct * sa, a * st],
            [0, sa, ca, d],
            [0, 0, 0, 1],
        ]
    )


def chain_kin_sym(chain: ChainParams, q: Sequence):
    """Symbolic forward kinematics for a chain."""
    sp = _sympy()
    T = sp.eye(4)
    q_idx = 0
    for link in chain.dh_params:
        if link.joint_type in ("revolute", "prismatic"):
            qi = q[q_idx]
            q_idx += 1
        else:
            qi = 0
        T = T * dh_transform_sym(link, qi)
    if q_idx != len(q):
        raise ValueError("Joint vector length does not match number of movable joints.")
    return T


def chain_footpoint_sym(chain: ChainParams, q: Sequence):
    """Symbolic end-effector position (3x1)."""
    T = chain_kin_sym(chain, q)
    return T[0:3, 3]


def jacobian_footpoint_sym(chain: ChainParams, q: Sequence):
    """Symbolic position Jacobian for the end-effector (3 x n)."""
    sp = _sympy()
    p = chain_footpoint_sym(chain, q)
    return sp.Matrix(p).jacobian(sp.Matrix(q))


def lambdify_chain_footpoint(chain: ChainParams, q: Sequence):
    """Return a NumPy-callable function for the end-effector position."""
    sp = _sympy()
    p = chain_footpoint_sym(chain, q)
    return sp.lambdify(q, p, "numpy")


def lambdify_chain_jacobian(chain: ChainParams, q: Sequence):
    """Return a NumPy-callable function for the end-effector Jacobian."""
    sp = _sympy()
    J = jacobian_footpoint_sym(chain, q)
    return sp.lambdify(q, J, "numpy")


def with_symbolic_params(chain: ChainParams, symbols: Iterable):
    """Return a copy of ChainParams with numeric fields replaced by symbols.

    Example:
        a1, a2 = sp.symbols("a1 a2")
        chain_sym = with_symbolic_params(chain, [a1, a2, ...])
    """
    sp = _sympy()
    sym_iter = iter(symbols)
    new_params = []
    for link in chain.dh_params:
        def _take(v):
            return next(sym_iter) if isinstance(v, (int, float)) else v

        new_params.append(
            replace(
                link,
                a=_take(link.a),
                alpha=_take(link.alpha),
                d=_take(link.d),
                theta_offset=_take(link.theta_offset),
            )
        )
    return ChainParams(dh_params=new_params)
