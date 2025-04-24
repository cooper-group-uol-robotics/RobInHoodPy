####################TODO remove when making this a pip package
import sys
import os 
file_path = sys.path.insert(1, os.path.dirname(os.path.abspath(__file__))+'/..')
####################

import math
import logging
import time
import datetime
from frankx import Affine, LinearRelativeMotion, Robot, Gripper
from robinhood.frankx_helpers import FrankxHelpers
from conf.configuration import *
from conf.workflow_config import *
from pylabware import RCTDigitalHotplate,XCalibur,QuantosQB1
from ..drivers.camera import CameraCapper, RSCamera
from .timer import Timer
from ..drivers.capper import Capper
from ..drivers.pumpholder import Holder
from ..drivers.shaker import Shaker
from ..drivers.lightbox import LightBox
from drivers.Filtbot.filt_machine import FiltMachine
from .workflow_helper import Workflow_Helper


class RobInHoodInspector():
    """
    This class connects with Panda robot.
    """
    def __init__(self, inst_logger = "test_logger", conf_path=FILENAME, ip=PANDA_IP, sim=False, vel=0.05 ):
        """
        This constructor takes as input the filename, ip and sim.
        : param inst_logger: str name for the instrument logger file.
        :param filename: is a string containing the file's path where the joints positions of the Panda robot were saved.
        :type: string
        :param ip: is a string containing the IP address of the Panda's robot API.
        :type: string
        :param sim: is a bool value that allows to run the code in sumulation mode when set to True 
        :type: bool
        :param vel: it is used to set the velocity of the robot which goes from 0.01 to 1.0
        :type: float
        """
        #self.cfg=read_json_cfg(conf_path)
        self.robot=None
        self.state=None
        self.ip=ip
        self.sim=sim
        self.vel=vel
        self.robot_connected=self.init_robot()
        ###### Robot control methods##################################	
    def init_robot(self):
        """
        This method stablishes connection with Panda robot when self.sim is set to True. TODO It is neccesary to work on the sim mode, which is currently not working. 
        :return: True when the robot is connected, False when the robot connection fails and True hen the sim mode (self.sim) is set to True
        :type: bool
        """
        if not self.sim:
            try:
                self.robot = FrankxHelpers(self.ip,self.vel)
                self.state = self.robot.robot.read_once()
                print(f'Panda robot connected to {self.ip}')
                return True
            except:
                print("Robot not connected...") 
                return False  	
        else:
            print("Robot running in testing mode.")
            return True
    
    def linear_motion(self,pose):
        self.robot.move_robot_x(pose)
        return
    def joint_motion(self,joints):
        self.robot.move_robot_j(joints)
    def inspect_rack(self):
        self.joint_motion([-0.02303354207465523, -0.6034788178561045, -0.009386303693056106, -1.5231378139332936, -0.043649802770879535, 0.7044200197278055, 0.7790021944219867])
        self.joint_motion([-1.6328059536281385, -0.5734210071647377, 0.21458031084828136, -1.3916960403876872, -0.04649895135290658, 0.6901212731168587, 0.7500545049034097])
        self.joint_motion([-1.702539307707178, -0.9279664513102749, 0.6152681235430534, -2.4812665662932814, 0.48589558421240914, 1.62926374525494, 2.621866312839091])
        input('Inspecting rack...')
        self.joint_motion([-1.6328059536281385, -0.5734210071647377, 0.21458031084828136, -1.3916960403876872, -0.04649895135290658, 0.6901212731168587, 0.7500545049034097])
        self.joint_motion([-0.02303354207465523, -0.6034788178561045, -0.009386303693056106, -1.5231378139332936, -0.043649802770879535, 0.7044200197278055, 0.7790021944219867])
        return
    def inspect_quantos(self):
        self.joint_motion([-0.02303354207465523, -0.6034788178561045, -0.009386303693056106, -1.5231378139332936, -0.043649802770879535, 0.7044200197278055, 0.7790021944219867])
        self.joint_motion([1.660128581799959, -0.6452941698373943, -0.23465103053851938, -1.5456929076849333, -0.03960211203826797, 0.7662701289918685, 0.8229499801173805])
        self.joint_motion([1.7302986266989455, -0.9260115279649436, -0.22521858482402668, -2.862327836321111, -0.15275696641030623, 1.5339040245241857, 0.8664757733590838])
        input('Inspecting quantos...')
        self.joint_motion([1.660128581799959, -0.6452941698373943, -0.23465103053851938, -1.5456929076849333, -0.03960211203826797, 0.7662701289918685, 0.8229499801173805])
        self.joint_motion([-0.02303354207465523, -0.6034788178561045, -0.009386303693056106, -1.5231378139332936, -0.043649802770879535, 0.7044200197278055, 0.7790021944219867])
        return
    def inspect_filtering_cartridge(self):
        self.joint_motion([-0.02303354207465523, -0.6034788178561045, -0.009386303693056106, -1.5231378139332936, -0.043649802770879535, 0.7044200197278055, 0.7790021944219867])
        self.joint_motion([1.232691785151929, -0.644565244666317, -0.2632882177373346, -1.9803763086617543, -0.10780123711956871, 1.360266422536638, -0.5206483014250793])
        self.joint_motion([1.8256919337050581, -0.6294897354945793, -0.42692593968123715, -2.1722880107143467, -0.28330350738101534, 1.5848448714680141, -0.817825827581187])
        input('Inspecting cartridge...')
        self.joint_motion([1.232691785151929, -0.644565244666317, -0.2632882177373346, -1.9803763086617543, -0.10780123711956871, 1.360266422536638, -0.5206483014250793])
        self.joint_motion([-0.02303354207465523, -0.6034788178561045, -0.009386303693056106, -1.5231378139332936, -0.043649802770879535, 0.7044200197278055, 0.7790021944219867])
        return
    def inspect_cartridges_rack(self):
        self.joint_motion([-0.02303354207465523, -0.6034788178561045, -0.009386303693056106, -1.5231378139332936, -0.043649802770879535, 0.7044200197278055, 0.7790021944219867])
        self.joint_motion([1.3242917193195398, -0.5940986870046248, -0.23680841785394197, -1.5097266106711045, -0.048567792024053806, 0.8347411236253618, 0.7744773020832499])
        self.joint_motion([1.6821634479823864, -0.9056772102640385, -0.38282422042228464, -1.9692345837208263, -0.29675100247633046, 1.1224129403255603, -1.0471628268532243])
        input('Inspecting rack...')
        self.joint_motion([1.3242917193195398, -0.5940986870046248, -0.23680841785394197, -1.5097266106711045, -0.048567792024053806, 0.8347411236253618, 0.7744773020832499])
        self.joint_motion([-0.02303354207465523, -0.6034788178561045, -0.009386303693056106, -1.5231378139332936, -0.043649802770879535, 0.7044200197278055, 0.7790021944219867])
        return