#!/usr/bin/env python

from __future__ import print_function

import random

import numpy as np
from pybullet_tools.utils import connect, load_model, disconnect, wait_for_user, create_box, set_point, dump_body, \
    TURTLEBOT_URDF, HideOutput, LockRenderer, joint_from_name, set_euler, get_euler, get_point, \
    set_joint_position, get_joint_positions, pairwise_collision, stable_z, wait_for_duration

# RGBA colors (alpha is transparency)
RED = (1, 0, 0, 1)
TAN = (0.824, 0.706, 0.549, 1)

def main(floor_width=2.0):
    # Creates a pybullet world and a visualizer for it
    connect(use_gui=True)

    # Bodies are described by an integer index
    floor = create_box(w=floor_width, l=floor_width, h=0.001, color=TAN) # Creates a tan box object for the floor
    set_point(floor, [0, 0, -0.001 / 2.]) # Sets the [x,y,z] translation of the floor

    obstacle = create_box(w=0.5, l=0.5, h=0.1, color=RED) # Creates a red box obstacle
    set_point(obstacle, [0.5, 0.5, 0.1 / 2.]) # Sets the [x,y,z] position of the obstacle
    print('Position:', get_point(obstacle))
    set_euler(obstacle, [0, 0, np.pi / 4]) #  Sets the [roll,pitch,yaw] orientation of the obstacle
    print('Orientation:', get_euler(obstacle))

    with LockRenderer(): # Temporarily prevents the renderer from updating for improved loading efficiency
        with HideOutput(): # Temporarily suppresses pybullet output
            robot = load_model(TURTLEBOT_URDF) # Loads a robot from a *.urdf file
            robot_z = stable_z(robot, floor) # Returns the z offset required for robot to be placed on floor
            set_point(robot, [0, 0, robot_z]) # Sets the z position of the robot
    dump_body(robot) # Prints joint and link information about robot

    # Joints are also described by an integer index
    # The turtlebot has explicit joints representing x, y, theta
    x_joint = joint_from_name(robot, 'x') # Looks up the robot joint named 'x'
    y_joint = joint_from_name(robot, 'y') # Looks up the robot joint named 'y'
    theta_joint = joint_from_name(robot, 'theta') # Looks up the robot joint named 'theta'
    joints = [x_joint, y_joint, theta_joint]

    random.seed(0) # Sets the random number generator state
    for i in range(10):
        x = random.uniform(-floor_width/2., floor_width/2.)
        set_joint_position(robot, x_joint, x) # Sets the current value of the x joint
        y = random.uniform(-floor_width/2., floor_width/2.)
        set_joint_position(robot, y_joint, y) # Sets the current value of the y joint
        theta = random.uniform(-np.pi, np.pi)
        set_joint_position(robot, theta_joint, theta) # Sets the current value of the theta joint

        values = get_joint_positions(robot, joints) # Obtains the current values for the specified joints
        print('Iteration {}) Joint values: {}'.format(i, values))
        collision = pairwise_collision(robot, obstacle) # Checks whether robot is currently colliding with obstacle
        print('Collision: {}'.format(collision))
        wait_for_duration(1.0) # Like sleep() but also updates the viewer
    wait_for_user() # Like raw_input() but also updates the viewer

    # Destroys the pybullet world
    disconnect()

if __name__ == '__main__':
    main()
