import numpy as np

from core.dtypes import ChainPose, ChainParams, JointVec, RobotPose

def pose_to_joint(pose: ChainPose) -> JointVec:
    return np.array([pose.coxa, pose.femur, pose.tibia], dtype=float)

def joint_to_pose(joint: JointVec) -> ChainPose:
    return ChainPose(coxa=joint[0], femur=joint[1], tibia=joint[2])

def pose_to_robotpose(p: ChainPose) -> RobotPose:
    return RobotPose(FL=p, FR=p, RL=p, RR=p)

LEG_POSES = {
    "STANCE": ChainPose(0.0, 0.0, 0.0),
    "LIFT":    ChainPose(0.0, 0.9, -0.9),
    "SWING":  ChainPose(0.0, 0.5, -0.5),
    "PLACE":  ChainPose(0.3, 0.2, -0.2),
}

ROBOT_POSES = {}    