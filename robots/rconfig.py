from typing import Sequence
import numpy as np
from sympy import Matrix, symbols
from core.dtypes import DHparam, ChainParams, IKParams, Vec3
from core.kinematics import chain_footpoint

LEG_IDS = ['FL', 'FR', 'RL', 'RR']

LEG_PHASE_OFFSETS = {
    'FL': 0.0,
    'FR': 0.5,
    'RL': 0.5,
    'RR': 0.0,
}

# Mirror factors: how each leg's foot position relates to FL
# FL is at (+x, +y), FR at (+x, -y), RL at (-x, +y), RR at (-x, -y)
LEG_MIRROR = {
    'FL': np.array([ 1.0,  1.0, 1.0]),
    'FR': np.array([ 1.0, -1.0, 1.0]),
    'RL': np.array([-1.0,  1.0, 1.0]),
    'RR': np.array([-1.0, -1.0, 1.0]),
}

# base_position at q=[0,0,0] is ~[0.060, 0.060, 0.070]
# Nominal pose raises body to BODY_HEIGHT while keeping the same x,y footprint
BODY_HEIGHT = 0.0947
_nominal_cache: dict | None = None

def FL_chain(theta_offsets=(0.0, 0.0, 0.0,)) -> ChainParams:
    """Define the Front Left Leg chain parameters."""
    o1, o2, o3 = theta_offsets
    theta = [o1, o2, o3]
    dh_params = [
        DHparam(a=0.084853, alpha=0.000000, d=0.000000, theta_offset=0.785398, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=theta[0], joint_type='revolute'),
        DHparam(a=0.040000, alpha=1.570796, d=0.000000, theta_offset=0.000000, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=theta[1], joint_type='revolute'),
        DHparam(a=0.035000, alpha=0.000000, d=0.000000, theta_offset=0.000000, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=-1.570796, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=theta[2], joint_type='revolute'),
        DHparam(a=0.070000, alpha=0.000000, d=0.000000, theta_offset=0.000000, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=-1.570796, d=0.000000, theta_offset=1.570796, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=-0.785398, joint_type='fixed')  # Virtual joint for frame alignment
    ]
    return ChainParams(dh_params=dh_params)

def FR_chain(theta_offsets=(0.0, 0.0, 0.0,)) -> ChainParams:
    """Define the Front Right Leg chain parameters."""
    o1, o2, o3 = theta_offsets
    theta = [o1, o2, o3]
    dh_params = [
        DHparam(a=0.084900, alpha=0.000000, d=0.000000, theta_offset=-0.785398, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=theta[0], joint_type='revolute'),
        DHparam(a=0.040000, alpha=1.570796, d=0.000000, theta_offset=0.000000, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=theta[1], joint_type='revolute'),
        DHparam(a=0.035000, alpha=0.000000, d=0.000000, theta_offset=0.000000, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=-1.570796, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=theta[2], joint_type='revolute'),
        DHparam(a=0.070000, alpha=0.000000, d=0.000000, theta_offset=0.000000, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=-1.570796, d=0.000000, theta_offset=1.570796, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=0.785398, joint_type='fixed')  # Virtual joint for frame alignment
    ]
    return ChainParams(dh_params=dh_params)

def RL_chain(theta_offsets=(0.0, 0.0, 0.0,)) -> ChainParams:
    """Define the Rear Left Leg chain parameters."""
    o1, o2, o3 = theta_offsets
    theta = [o1, o2, o3]
    dh_params = [
        DHparam(a=0.084900, alpha=0.000000, d=0.000000, theta_offset=2.356194, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.035000, alpha=0.000000, d=0.000000, theta_offset=theta[0], joint_type='revolute'),
        DHparam(a=0.040000, alpha=1.570796, d=0.000000, theta_offset=0.000000, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=theta[1], joint_type='revolute'),
        DHparam(a=0.035000, alpha=0.000000, d=0.000000, theta_offset=0.000000, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=-1.570796, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=theta[2], joint_type='revolute'),
        DHparam(a=0.070000, alpha=0.000000, d=0.000000, theta_offset=0.000000, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=-1.570796, d=0.000000, theta_offset=1.570796, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=-2.356194, joint_type='fixed')  # Virtual joint for frame alignment
    ]
    return ChainParams(dh_params=dh_params)

def RR_chain(theta_offsets=(0.0, 0.0, 0.0,)) -> ChainParams:
    """Define the Rear Right Leg chain parameters."""
    o1, o2, o3 = theta_offsets
    theta = [o1, o2, o3]
    dh_params = [
        DHparam(a=0.084900, alpha=0.000000, d=0.000000, theta_offset=-2.356194, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.035000, alpha=0.000000, d=0.000000, theta_offset=theta[0], joint_type='revolute'),
        DHparam(a=0.040000, alpha=1.570796, d=0.000000, theta_offset=0.000000, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.050000, alpha=0.000000, d=0.000000, theta_offset=theta[1], joint_type='revolute'),
        DHparam(a=0.035000, alpha=0.000000, d=0.000000, theta_offset=0.000000, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=-1.570796, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=theta[2], joint_type='revolute'),
        DHparam(a=0.070000, alpha=0.000000, d=0.000000, theta_offset=0.000000, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=-1.570796, d=0.000000, theta_offset=1.570796, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=2.356194, joint_type='fixed')  # Virtual joint for frame alignment
    ]
    return ChainParams(dh_params=dh_params)

def nominal_from_height(h: float) -> tuple[np.ndarray, dict[str, Vec3]]:
    """IK-solve for joint angles that place feet at the zero-pose x,y
    footprint but with the body at height *h*.

    Returns (q_nominal, nominal_feet_dict).
    """
    from core.inverse_kinematics import LegIK

    chain = FL_chain()
    ik = LegIK(chain, T0=Matrix.eye(4))

    # foot x,y at zero pose (flat links)
    p_zero = np.array([float(x) for x in chain_footpoint(chain, [0.0, 0.0, 0.0])])
    p_target = np.array([p_zero[0], p_zero[1], -h])

    params = IKParams(alpha=0.55, max_dq=0.3, max_iters=200, tol=1e-6)
    q_nom, info = ik.solve(np.zeros(3), p_target, params)
    if not info.ok:
        raise RuntimeError(f"nominal_from_height({h}): IK did not converge (err={info.err:.2e})")

    p_fl = ik.fk_np(q_nom)
    feet = {leg: p_fl * LEG_MIRROR[leg] for leg in LEG_IDS}
    return q_nom, feet


def _get_nominal() -> dict:
    """Compute and cache the nominal configuration."""
    global _nominal_cache
    if _nominal_cache is None:
        q, feet = nominal_from_height(BODY_HEIGHT)
        _nominal_cache = {'q': q, 'feet': feet}
    return _nominal_cache


def get_q_nominal() -> np.ndarray:
    """Return joint angles for standing at BODY_HEIGHT (feet stay planted)."""
    return _get_nominal()['q'].copy()


def nominal_feet() -> dict[str, Vec3]:
    """Return nominal foot positions for all legs at BODY_HEIGHT."""
    return dict(_get_nominal()['feet'])


# def FL_chain(theta_offsets=(0.0, 0.0, 0.0)) -> ChainParams:
#     """Define the Front Left Leg chain parameters."""

#     # theta_1, theta_2, theta_3 = symbols('theta_1 theta_2 theta_3', real=True)
#     o1, o2, o3 = theta_offsets
#     theta = [o1, o2, o3]
#     dh_params = [
#         DHparam(a=0.084853, alpha=0.0, d=0.0, theta_offset=0.785398, joint_type='fixed', isvirtual=True),
#         DHparam(a=0.0, alpha=0.0, d=0.0, theta_offset=theta[0], joint_type='revolute'),
#         DHparam(a=0.04, alpha=1.570796, d=0.0, theta_offset=0.0, joint_type='fixed', isvirtual=True),
#         DHparam(a=0.0, alpha=0.0, d=0.0, theta_offset=-0.785398, joint_type='fixed', isvirtual=True),
#         DHparam(a=0.0, alpha=0.0, d=0.0, theta_offset=theta[1], joint_type='revolute'),
#         DHparam(a=0.035, alpha=0.0, d=0.0, theta_offset=0.0, joint_type='fixed', isvirtual=True),
#         DHparam(a=0.0, alpha=0.0, d=0.0, theta_offset=-0.785398, joint_type='fixed', isvirtual=True),
#         DHparam(a=0.0, alpha=0.0, d=0.0, theta_offset=theta[2], joint_type='revolute'),
#         DHparam(a=0.07, alpha=0.0, d=0.0, theta_offset=0.0, joint_type='fixed', isvirtual=True),
#         DHparam(a=0.0, alpha=-1.570796, d=0.0, theta_offset=1.570796, joint_type='fixed', isvirtual=True),
#         DHparam(a=0.0, alpha=0.0, d=0.0, theta_offset=-0.785398, joint_type='fixed', isvirtual=True),
#     ]
#     return ChainParams(dh_params=dh_params)

    # theta_1, theta_2, theta_3 = symbols('theta_1 theta_2 theta_3', real=True)
    # dh_params = [
    #     {'a': 0.084853, 'alpha': 0.000000, 'd': 0.000000, 'theta': 0.785398, 'type': 'fixed'},  # Virtual joint for frame alignment
    #     {'a': 0.000000, 'alpha': 0.000000, 'd': 0.000000, 'theta': theta_1 + 0.000000, 'type': 'revolute'},
    #     {'a': 0.040000, 'alpha': 1.570796, 'd': 0.000000, 'theta': 0.000000, 'type': 'fixed'},  # Virtual joint for frame alignment
    #     {'a': 0.000000, 'alpha': 0.000000, 'd': 0.000000, 'theta': -0.785398, 'type': 'fixed'},  # Virtual joint for frame alignment
    #     {'a': 0.000000, 'alpha': 0.000000, 'd': 0.000000, 'theta': theta_2 + 0.000000, 'type': 'revolute'},
    #     {'a': 0.035000, 'alpha': 0.000000, 'd': 0.000000, 'theta': 0.000000, 'type': 'fixed'},  # Virtual joint for frame alignment
    #     {'a': 0.000000, 'alpha': 0.000000, 'd': 0.000000, 'theta': -0.785398, 'type': 'fixed'},  # Virtual joint for frame alignment
    #     {'a': 0.000000, 'alpha': 0.000000, 'd': 0.000000, 'theta': theta_3 + 0.000000, 'type': 'revolute'},
    #     {'a': 0.070000, 'alpha': 0.000000, 'd': 0.000000, 'theta': 0.000000, 'type': 'fixed'},  # Virtual joint for frame alignment
    #     {'a': 0.000000, 'alpha': -1.570796, 'd': 0.000000, 'theta': 1.570796, 'type': 'fixed'},  # Virtual joint for frame alignment
    #     {'a': 0.000000, 'alpha': 0.000000, 'd': 0.000000, 'theta': -0.785398, 'type': 'fixed'}  # Virtual joint for frame alignment
    # ]
    # return ChainParams(dh_params=dh_params)