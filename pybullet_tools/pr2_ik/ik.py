from pybullet_tools.pr2_ik.ikLeft import leftIK, leftFK
from pybullet_tools.pr2_ik.ikRight import rightIK, rightFK
from pybullet_tools.utils import matrix_from_quat, point_from_pose, quat_from_pose, quat_from_matrix, Pose, multiply, elapsed_time, \
    get_link_pose, link_from_name, joints_from_names, get_joint_positions, get_joint_limits, joint_from_name, invert, \
    get_joint_position, violates_limits, INF
from pybullet_tools.pr2_utils import PR2_GROUPS, arm_from_arm

import random
import time

ARM_FK = {
    'left': leftFK,
    'right': rightFK,
}
ARM_IK = {
    'left': leftIK,
    'right': rightIK,
}

BASE_LINK = 'base_link'
TORSO_JOINT = 'torso_lift_joint'

UPPER_JOINT = {
    'left': 'l_upper_arm_roll_joint',
    'right': 'r_upper_arm_roll_joint',
}

# tool = l_gripper_tool_frame | r_gripper_tool_frame
# upper = l_upper_arm_roll_joint | r_upper_arm_roll_joint
# torso = torso_lift_joint

#def get_prefix(arm):
#    return arm[0]

def or_from_pyb_quat(quat):
    x, y, z, w = quat
    return [w, x, y, z]

def pyb_from_or_quat(quat):
    w, x, y, z = quat
    return [x, y, z, w]

def get_base_pose(robot):
    return get_link_pose(robot, link_from_name(robot, BASE_LINK))

def get_arm_joints(robot, arm):
    return joints_from_names(robot, PR2_GROUPS['torso'] + PR2_GROUPS[arm_from_arm(arm)])

#####################################

def forward_kinematics(arm, conf):
    # base_link -> l_gripper_tool_frame | r_gripper_tool_frame
    assert len(conf) == 8
    fk_fn = ARM_FK[arm]
    pose = fk_fn(list(conf))
    pos, rot = pose
    quat = quat_from_matrix(rot) # [X,Y,Z,W]
    return pos, quat
    # switch from [r, i, j, k] to [i, j, k, r]
    #quat = quat if quat.real >= 0 else -quat  # solves q and -q being same rotation

def get_tool_pose(robot, arm):
    # TODO: compute static transform from base_footprint -> base_link
    tool_pose = forward_kinematics(arm, get_joint_positions(robot, get_arm_joints(robot, arm)))
    return multiply(get_base_pose(robot), tool_pose)

#####################################

def inverse_kinematics(arm, pose, torso, upper):
    ik_fn = ARM_IK[arm]
    pos = point_from_pose(pose)
    rot = matrix_from_quat(quat_from_pose(pose)).tolist()
    solutions = ik_fn(list(rot), list(pos), [torso, upper])
    if solutions is None:
        return []
    return solutions

def get_limits(robot, joint, limits):
    if limits is False:
        return get_joint_limits(robot, joint)
    elif limits is None:
        torso_value = get_joint_position(robot, joint)
        return torso_value, torso_value
    return limits

#def sample_ik(robot, arm, target_pose, torso_limits, upper_limits):
#    arm_joints = get_arm_joints(robot, arm)
#    torso = random.uniform(*torso_limits)
#    upper = random.uniform(*upper_limits)
#    return [q for q in inverse_kinematics(arm, target_pose, torso, upper)
#           if not violates_limits(robot, arm_joints, q)]

def get_ik_generator(robot, arm, world_pose, torso_limits=False, upper_limits=False):
    target_pose = multiply(invert(get_base_pose(robot)), world_pose)
    torso_limits = get_limits(robot, joint_from_name(robot, TORSO_JOINT), torso_limits)
    upper_limits = get_limits(robot, joint_from_name(robot, UPPER_JOINT[arm]), upper_limits)
    arm_joints = get_arm_joints(robot, arm)
    while True:
        torso = random.uniform(*torso_limits)
        upper = random.uniform(*upper_limits)
        yield [q for q in inverse_kinematics(arm, target_pose, torso, upper)
               if not violates_limits(robot, arm_joints, q)]

def sample_tool_ik(robot, arm, tool_pose, max_attempts=10, **kwargs):
    generator = get_ik_generator(robot, arm, tool_pose, **kwargs)
    for _ in range(max_attempts):
        try:
            solutions = next(generator)
            if solutions:
                return random.sample(solutions)
        except StopIteration:
            break
    return None

#####################################

# def accelerate_list_generator(generator, max_attempts=1, max_time=np.inf):
#     while True:
#         start_time = time.time()
#         for i in range(max_attempts):
#             if max_time <= elapsed_time(start_time):
#                 break
#             sequence = next(generator)
#             if sequence:
#                 yield sequence
#                 break
