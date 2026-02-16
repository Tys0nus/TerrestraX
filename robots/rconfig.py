from typing import Sequence
from core.dtypes import DHparam, ChainParams
from sympy import symbols

def FL_chain(theta_offsets=(0.0, 0.0, 0.0)) -> ChainParams:
    """Define the Front Left Leg chain parameters."""

    # theta_1, theta_2, theta_3 = symbols('theta_1 theta_2 theta_3', real=True)
    o1, o2, o3 = theta_offsets
    theta = [o1, o2, o3]
    dh_params = [
        DHparam(a=0.084853, alpha=0.0, d=0.0, theta_offset=0.785398, joint_type='fixed', isvirtual=True),
        DHparam(a=0.0, alpha=0.0, d=0.0, theta_offset=theta[0], joint_type='revolute'),
        DHparam(a=0.04, alpha=1.570796, d=0.0, theta_offset=0.0, joint_type='fixed', isvirtual=True),
        DHparam(a=0.0, alpha=0.0, d=0.0, theta_offset=-0.785398, joint_type='fixed', isvirtual=True),
        DHparam(a=0.0, alpha=0.0, d=0.0, theta_offset=theta[1], joint_type='revolute'),
        DHparam(a=0.035, alpha=0.0, d=0.0, theta_offset=0.0, joint_type='fixed', isvirtual=True),
        DHparam(a=0.0, alpha=0.0, d=0.0, theta_offset=-0.785398, joint_type='fixed', isvirtual=True),
        DHparam(a=0.0, alpha=0.0, d=0.0, theta_offset=theta[2], joint_type='revolute'),
        DHparam(a=0.07, alpha=0.0, d=0.0, theta_offset=0.0, joint_type='fixed', isvirtual=True),
        DHparam(a=0.0, alpha=-1.570796, d=0.0, theta_offset=1.570796, joint_type='fixed', isvirtual=True),
        DHparam(a=0.0, alpha=0.0, d=0.0, theta_offset=-0.785398, joint_type='fixed', isvirtual=True),
    ]
    return ChainParams(dh_params=dh_params)

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