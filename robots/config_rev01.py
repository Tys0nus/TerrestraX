from core.dtypes import DHparam, ChainParams, JointVec
import numpy as np

def FL_chain() -> ChainParams:
    """Define the Front Left Leg chain parameters."""
    dh_params = [
        DHparam(a=0.084853, alpha=0.000000, d=0.000000, theta_offset=0.785398, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=0.000000, joint_type='revolute'),
        DHparam(a=0.040000, alpha=1.570796, d=0.000000, theta_offset=0.000000, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=-0.785398, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=0.000000, joint_type='revolute'),
        DHparam(a=0.035000, alpha=0.000000, d=0.000000, theta_offset=0.000000, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=-0.785398, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=0.000000, joint_type='revolute'),
        DHparam(a=0.070000, alpha=0.000000, d=0.000000, theta_offset=0.000000, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=-1.570796, d=0.000000, theta_offset=1.570796, joint_type='fixed'),  # Virtual joint for frame alignment
        DHparam(a=0.000000, alpha=0.000000, d=0.000000, theta_offset=-0.785398, joint_type='fixed')  # Virtual joint for frame alignment
    ]

    return ChainParams(dh_params=dh_params)