import numpy as np
#from frankx import Affine, LinearRelativeMotion, Robot, JointMotion, Kinematics, ImpedanceMotion, Gripper
from time import sleep

class FrankxHelpers():
    def __init__(self, host, vel=0.01):
        self.robot = Robot(host)
        self.gripper = Gripper(host)
        self.robot.recover_from_errors()
        # self.gripper.recover_from_errors()
        # Set velocity, acceleration and jerk to 10% of the maximum
        self.robot.set_dynamic_rel(vel) 
        self.robot.current_pose()


    def reset_robot(self):
        self.robot.read_once()
        return
    
    def open_gripper(self):
        self.gripper.move(0.05)
        #self.gripper.open()
        return

    def open_gripper_set_width(self, width):
        # gripper.move(50.0); // [mm]
        self.gripper.move(width)
        return
    def close_gripper(self):
        self.gripper.clamp()
        return


    def recover_from_errors(self):
        self.robot.recover_from_errors()
        return



    def move_robot_j(self, position_j):

        """
        Move robot in the joint space (q1 ... q7) e.g. position_j = JointMotion([-0.06801003708232913, -0.7946914721790113, -0.025459439155041123, -3.0178200251866536, 0.008655966668493218, 2.2786499461597867, 0.7173295130719647])

        """
        self.robot.move(JointMotion(position_j))
        return

    def move_robot_x(self, position_x):
        """
        Move robot in the cartesian space (x, y, z, a, b, c) e.g. position_x = LinearMotion(Affine(0.2, -0.4, 0.3, math.pi / 2, 0.0, 0.0))
        """
        
        self.robot.move(position_x)
        return

    def get_cartesian_pose(self):
        """
        Get robot pose in the cartesian space (x, y, z, a, b, c)
        """
        current_pose = self.robot.current_pose()
        cartesian_pose = np.array([current_pose.x, current_pose.y, current_pose.z])
        return cartesian_pose

    def get_joint_pose(self):
        """
        Get robot pose in the joint space (q1 .. q7)
        """
        state = self.robot.read_once()
        return (state.q)
    
    def get_state_j(self):
        """
        Get robot state in the joint space (q1 .. q7, dq1 .. dq7, tau1 .. tau7)
        """
        state = self.robot.read_once()
        return (state.q, state.dq, state.tau_J)     

    def get_desired_state_j(self):
        """
        Get desired robot state in the joint space (q1 .. q7, dq1 .. dq7, ddq1 .. ddq7, tau1 .. tau7)
        """
        state = self.robot.read_once()
        return (state.q_d, state.dq_d, state.ddq_d, state.tau_J_d)       

    
    def forward_kinematics(self, q_current):
        """
        Compute forward kinematics i.e. (q1 .. q7) - > (x, y, z, a, b, c)
        """
        x = Affine(Kinematics.forward(q_current))
        return x

    def inverse_kinematics(self, x_current, q_current):
        """
        Compute inverse kinematics i.e. (x, y, z, a, b, c) -> (q1 .. q7)
        """        

        # Franka has 7 DoFs, so what to do with the remaining Null space?
        null_space = NullSpaceHandling(2, 1.4) # Set elbow joint to 1.4

        # Inverse kinematic with target, initial joint angles, and Null space configuration
        q_new = Kinematics.inverse(x_current.vector(), q_current, null_space)

    def impedance_controller(self, target_goal):

        # Define and move forwards
        self.robot.move(target_goal)

        # Define and move forwards
        impedance_motion = ImpedanceMotion(2000.0, 200.0)
        robot_thread = self.robot.move_async(impedance_motion)

        s = self.get_state_j()
        print(s)
        sleep(0.05)

        # initial_target = impedance_motion.target
        # print('initial target: ', initial_target)

        # sleep(0.5)

        # new_target = JointMotion([-0.06801003708232913, -0.7946914721790113, -0.025459439155041123, -3.0178200251866536, 0.008655966668493218, 2.2786499461597867, 0.7173295130719647])

        # impedance_motion.target = new_target
        # print('set new target: ', impedance_motion.target)

        # sleep(2.0)

        # impedance_motion.finish()
        # robot_thread.join()
        # print('motion finished')
        # robot_thread = self.robot.move_async(impedance_motion)

        # sleep(0.05)

        # initial_target = impedance_motion.target


    def add_constraints(self):
        # Stop motion if the overall force is greater than 30N
        d1 = MotionData().with_reaction(Reaction(Measure.ForceXYZNorm() > 30.0))

        # Apply reaction motion if the force in negative z-direction is greater than 10N
        d2 = MotionData().with_reaction(Reaction(Measure.ForceZ() < -10.0), reaction_motion)

        # Stop motion if its duration is above 30s
        d3 = MotionData().with_reaction(Reaction(Measure.Time() >= 30.0))

        # e.g. robot.move(m2, d2)

        # # Check if the reaction was triggered
        # if d2.has_fired:
        #     robot.recover_from_errors()
        #     print('Force exceeded 10N!')
