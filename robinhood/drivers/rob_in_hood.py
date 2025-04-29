


####################

import math
import logging
import time
import datetime
from typing import Union
from frankx import Affine, LinearRelativeMotion, Robot, Gripper
from ..utils.frankx_helpers import FrankxHelpers
from ..config.configuration import *
from ..config.workflow_config import *
from ..config.configuration import *
from pylabware import RCTDigitalHotplate,XCalibur,QuantosQB1,C3000SyringePump
from ..drivers.camera import CameraCapper, RSCamera
from ..utils.timer import Timer
from ..drivers.capper import Capper
from ..drivers.pumpholder import Holder
from ..drivers.shaker import Shaker
from ..drivers.lightbox import LightBox
from ..drivers.Filtbot.filt_machine import FiltMachine
from ..utils.workflow_helper import Workflow_Helper

from ..config.workflow_config import PUMP_PORT_ASSIGNMENTS
####################TODO remove when making this a pip package
import sys
import os 
file_path = sys.path.insert(1, os.path.dirname(os.path.abspath(__file__))+'/..')



class RobInHood():
    """
    This class connects with Panda robot.
    """
    def __init__(self, inst_logger = "test_logger", conf_path=FILENAME, ip=PANDA_IP, sim=False, vel=0.05):
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

        self._pump_1_primed_solvent = None #port number of solvent primed in dispense line of the dispense pump_1
        self._pump_2_primed_solvent = None #port nummber of the solvent primed in the dispense line of dispense pump_2
        self._cartridge_in_quantos = None #cartridge position on rack of cartridge currently on the quantos
        
        self.pump_port_assignments = PUMP_PORT_ASSIGNMENTS #dictionary with the ports of the dispense pumps

        self.start_system_logger(inst_logger)

        if not sim:
            #Runs workflow config helper object - looks for config in relevant files, creates output path for data (not logs)
            self.workflow_helper = Workflow_Helper(config_path=SETUP_PATH, data_path=DATA_PATH)
            self.dispense_dict,self.dispense_dict_meta, self.quantos_dict, self.filt_dict, self.sample_dict = self.workflow_helper.workflow_setup()
        else:
             self.dispense_dict, self.quantos_dict, self.filt_dict, self.sample_dict= {},{},{},{} 
        
        self.capper=Capper(camera_id=CAPPER_CAMERA_ID)
        self.holder=Holder()
        #self.shaker=Shaker()
        
        self.filt_machine = FiltMachine(machine_port=FILTERINGSTATION_PORT, pump_port=FILTRATIONPUMP_PORT, switch_address="1", port_config=self.filt_dict)
        self.ika=RCTDigitalHotplate(device_name="IKA", connection_mode='serial', address='', port= IKA_PORT)
        
        
        
        
        self.pump = XCalibur(self.pump_port_assignments["Dispense_1"]["name"], 'serial', port = PUMP_PORT, switch_address="0",address="1", syringe_size= "1.0mL")
        self.pump_2 = C3000SyringePump(self.pump_port_assignments["Dispense_2"]["name"],"serial", port = ACID_PUMP_PORT, connection_mode="serial", address="1", switch_address="0", valve_type="6PORT_DISTR", syringe_size="12.5mL")
        
        
        self.quantos=QuantosQB1(device_name="QUANTOS", connection_mode="serial", port=QUANTOS_PORT)
        
        self.timer=Timer()
        self.lightbox=LightBox(camera_id=LIGHTBOX_CAMERA_ID)

        self.camera_connected=self.init_camera()
        self.ika_connected=self.init_ika()
        self.pump_connected=self.init_pump()
        self.pump2_connected =self.init_acid_pump()
        self.quantos_connected=self.init_quantos()
        self.filt_machine_connected = self.init_filt_machine()
        self.robot_connected=self.init_robot()
        self.devices_connected_report()
        self.hold_position()
    
    def linear_motion(self,pose):
        state=self.robot.robot.read_once()
        state=self.robot.robot.read_once()
        state=self.robot.robot.read_once()
        #self._logger.info('Pose: ', self.robot.robot.current_pose())
        #self._logger.info('Joints: ', state.q)
        self.robot.move_robot_x(pose)
        return
    def devices_connected_report(self): #TODO init filt machine
        """
        Terminates the program if one of the devices is not available.
        """
        if not self.camera_connected:
            self._logger.error("Capper camera is not available.")
        if not self.ika_connected:
           self._logger.error("IKA station is not available.")
        if not self.pump_connected:
           self._logger.error("XCalibur Pump is not available.")
        if not self.filt_machine_connected:
            self._logger.error("Filtering machine not connected")
        if not self.quantos_connected:
            self._logger.error("Quantos is not connected.")
            exit()
        if not self.robot_connected:
            self._logger.error("Robot not available or the emergency stop button is activated.") #removed pump connection check
        if not self.robot_connected: #removed camera
            self._logger.error("Terminating the program.")
            #if self.camera_connected:
            #    self.camera.stop_streaming()
            exit()
    #### Lightbox methods ###########################
    def open_lightbox(self):
        self.lightbox.opening_lightbox()
    def close_lightbox(self):
        self.lightbox.closing_lightbox()
    def light_on(self):
        self.lightbox.light_on()
    def light_off(self):
        self.lightbox.light_off()
    def save_picture_from_lightbox(self,dye_name="",solid_name="",path=""):
        self.lightbox.take_picture(dye_name=dye_name,solid_name=solid_name,path=path)
    #### Shaker control methods #####################
    def shaker_on(self):
        self.shaker.on()
    def shaker_off(self):
        self.shaker.off()
    #### Capper control methods #####################
    def cap(self):
        self._logger.info("Capping...")
        self.capper.right()
        time.sleep(90)
        self.capper.left()
        time.sleep(90)
    def check_capping(self):
        if self.capper.check_capping():
            self._logger.info("Capping process succesful.")
        else:
            self._logger.warning("Capping failed, please cap manually.")
            while True:
                self._logger.warning('Continue running workflow?(y/n)')
                yn=input()
                if yn =='y' or yn =='Y':
                    self._logger.info("Resuming workflow.")
                    break
                elif yn == 'n' or yn == 'N':
                    self._logger.info("Terminating workflow.")
                    exit() 
        time.sleep(5)
    #### Camera control methods #####################
    def init_camera(self):
        """
        Returns True when connected to a camera and False otherwise. 
        """
        try:
            self.camera_connected=self.camera.init_camera()
            self.camera.start_streaming()
            return self.camera_connected
        except Exception as e:
            return False
   

    ###### IKA control methods ###################################
    def init_ika(self,default_speed=200):
        """
        Connects to IKA and initialises at stirring speed 100. 
        
        Returns True when IKA has been connected, False otherwise.
        """
        self._logger.info("Connecting IKA RCT digital..")
        try:
            self.ika.connect()
            time.sleep(2)
            self.ika.is_connected()
            self._logger.info("IKA RCT digital connected.")
            time.sleep(1.5)
            self.ika.set_speed(default_speed)
            self._logger.info(f'Stiring velocity set to {default_speed}.')
            time.sleep(1.5)
            temperature=self.ika.get_temperature()
            self._logger.info(f'Current temperature: {temperature}.')
            return True
        except:
            self._logger.error("IKA RCT not connected.")
            return False
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
                self._logger.info(f'Panda robot connected to {self.ip}')
                #self._logger.info('Current Pose: ', self.robot.robot.current_pose())
                #self._logger.info('O_TT_E: ', self.state.O_T_EE)
                #self._logger.info('Joints: ', self.state.q)
                #self._logger.info('Elbow: ', self.state.elbow)
                return True
            except:
                self._logger.error("Robot not connected...") 
                return False  	
        else:
            self._logger.warning("Robot running in testing mode.")
            return True
	
    ##################################
	# Cartridge Manipulation methods #
    ##################################	
    def vial_pump_to_lightbox(self):
        '''
        
        '''
        self.linear_motion([0.024211, -0.466303, 0.389817, -1.587130, 0.0, 0.0])
        self.robot.gripper.clamp()
        self.linear_motion([0.024211, -0.466303, 0.439817, -1.587130, 0.0, 0.0])
        self.linear_motion([0.024211,  -0.286303, 0.439817, -1.587130, 0.0, 0.0])
        self.linear_motion([0.024211,  -0.286303, 0.439817, 0.001, 0.0, 0.0])
        self.linear_motion([0.024211,  -0.286303, 0.219817, 0.001, 0.0, 0.0])
        self.linear_motion([0.094211,  -0.286303, 0.224817, 0.001, 0.0, 0.0])
        self.linear_motion([0.124211,  -0.286303, 0.224817, 0.001, 0.0, 0.0])
        self.linear_motion([0.134211,  -0.286303, 0.223317, 0.001, 0.0, 0.0])
        self.linear_motion([0.134211,  -0.260303, 0.223317, 0.001, 0.0, 0.0])
        self.robot.open_gripper_set_width(0.03)
        self.linear_motion([0.034211,  -0.260303, 0.223317, 0.001, 0.0, 0.0])

    def vial_lightbox_to_pump(self):
        '''
        
        '''
        self.linear_motion([0.134211,  -0.260303, 0.223317, 0.001, 0.0, 0.0])
        self.robot.gripper.clamp()
        self.linear_motion([0.134211,  -0.286303, 0.223317, 0.001, 0.0, 0.0])
        self.linear_motion([0.124211,  -0.286303, 0.224817, 0.001, 0.0, 0.0])
        self.linear_motion([0.094211,  -0.286303, 0.224817, 0.001, 0.0, 0.0])
        self.linear_motion([0.024211,  -0.286303, 0.219817, 0.001, 0.0, 0.0])
        self.linear_motion([0.024211,  -0.286303, 0.439817, 0.001, 0.0, 0.0])
        self.linear_motion([0.024211,  -0.286303, 0.439817, -1.587130, 0.0, 0.0])
        self.linear_motion([0.024211, -0.466303, 0.439817, -1.587130, 0.0, 0.0])
        self.linear_motion([0.024211, -0.466303, 0.389817, -1.587130, 0.0, 0.0])
        self.robot.open_gripper_set_width(0.03)

    def pick_and_place_cartridge_in_quantos(self, cartridge_number = 1):
        """
        Picks the cartridge from its holder.
        Terminates the program if the quantos front door is closed in order to avoid any collisions.  
        """
        self.check_quantos_door_position()
        try:
            self._logger.info("Robot picking up cartridge ... ")
            self.robot.open_gripper_set_width(0.03)
            self.robot.move_robot_j([1.6350166825077042, -0.3914084763736055, -0.2136805891948834, -1.3643024899905856, -0.006134169170864666, 0.8799257986810473, 0.791025193176184])
            self.robot.move_robot_j([1.6407204749960649, -0.8904579096760666, -0.12368042052210422, -1.842811449837266, -0.008949056352705547, 0.9683798163202072, 0.7932483173135283])
            self.robot.move_robot_j([1.8286558759668823, -0.8510085091675601, -0.1403388809725381, -1.8050143277519628, -0.03595990048183335, 0.9802799679167741, -0.6215820595326329])
            self.linear_motion([0.015165, 0.182399, 0.68205, 3.1414, 0.0, 0.0])
            ##cartridge_1
            if cartridge_number==1:
                self.linear_motion([0.0, 0.1895, 0.693205, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.060, 0.1895, 0.693205, 3.1414, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([-0.060, 0.1895, 0.699405, 3.1414, 0.0, 0.0])
                self.linear_motion([0.0, 0.1895, 0.699405, 3.1414, 0.0, 0.0])
            if cartridge_number==2:
                self.linear_motion([0.0, 0.1895, 0.621205, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.0595, 0.1895, 0.621205, 3.1414, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([-0.0595, 0.1895, 0.623205, 3.1414, 0.0, 0.0])
                self.linear_motion([0.0, 0.1895, 0.623205, 3.1414, 0.0, 0.0])
            if cartridge_number==3:
                self.linear_motion([0.0, 0.1895, 0.549905, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.059, 0.1895, 0.549905, 3.1414, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([-0.059, 0.1895,0.551905, 3.1414, 0.0, 0.0])
                self.linear_motion([0.0, 0.1895,0.551905, 3.1414, 0.0, 0.0])
            if cartridge_number==4:
                self.linear_motion([0.0, 0.1885, 0.478905, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.059, 0.1885, 0.478905, 3.1414, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([-0.059, 0.1885,0.480905, 3.1414, 0.0, 0.0])
                self.linear_motion([0.0, 0.1885,0.480905, 3.1414, 0.0, 0.0])
            if cartridge_number==5:
                self.linear_motion([0.0, 0.1885,0.406705, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.058, 0.1885, 0.406705, 3.1414, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([-0.058, 0.1885,0.408705, 3.1414, 0.0, 0.0])
                self.linear_motion([0.0, 0.1885,0.408705, 3.1414, 0.0, 0.0])
            if cartridge_number==6:
                self.linear_motion([0.0, 0.2335, 0.693905, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.0605, 0.2335, 0.693905, 3.1414, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([-0.0605, 0.2335, 0.696405, 3.1414, 0.0, 0.0])
                self.linear_motion([0.0, 0.2335, 0.696405, 3.1414, 0.0, 0.0])
            if cartridge_number==7:
                self.linear_motion([0.0, 0.2355, 0.622405, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.058, 0.2355, 0.622405, 3.1414, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([-0.058, 0.2355, 0.624905, 3.1414, 0.0, 0.0])
                self.linear_motion([0.0, 0.2355, 0.624905, 3.1414, 0.0, 0.0])
            if cartridge_number==8:
                self.linear_motion([0.0, 0.235, 0.550755, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.058, 0.235, 0.550755, 3.1414, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([-0.058, 0.235,0.552755, 3.1414, 0.0, 0.0])
                self.linear_motion([0.0, 0.235, 0.552755, 3.1414, 0.0, 0.0])
                ##
            if cartridge_number==9:
                self.linear_motion([0.0, 0.234, 0.479555, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.057, 0.234, 0.479555, 3.1414, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([-0.057, 0.234,0.481555, 3.1414, 0.0, 0.0])
                self.linear_motion([0.0, 0.234, 0.481555, 3.1414, 0.0, 0.0])
                ##
            if cartridge_number==10:
                self.linear_motion([0.0, 0.234, 0.407855, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.057, 0.234, 0.407855, 3.1414, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([-0.057, 0.234,0.409855, 3.1414, 0.0, 0.0])
                self.linear_motion([0.0, 0.234, 0.409855, 3.1414, 0.0, 0.0])
            ####
            self.robot.move_robot_j([1.6675251447777997, -1.0275887485136066, -0.09035444692320839, -2.5317370912708634, -0.1183671841157807, 1.5240614581647351, 0.9499086411967872])
            self.robot.move_robot_j([1.380799593490466, -0.4352248667580561, -0.2281504641854476, -2.730614678848585, -0.12271172765617813, 2.31335698694653, 0.8155934429334268])
            self.robot.move_robot_j([1.623493001904404, -0.09582463145187611, -0.16833146013466532, -2.747920169294928, -0.12130647404896713, 2.6593146539794073, 0.7788315169190367])
            self.robot.move_robot_j( [1.6896320291805316, 0.01244918198713608, -0.06258759492568845, -2.6080483697255454, -0.12033771546343165, 2.661281414525643, 0.9884846218600867])
            self.linear_motion([-0.022624, 0.445206, 0.149430, math.pi/2, 0.0, 0.0])
            self.linear_motion([-0.022624, 0.445206, 0.154930, math.pi/2, 0.0, 0.0])
            self.linear_motion([-0.020624, 0.445206, 0.154930, math.pi/2, 0.0, 0.0])
            self.linear_motion([-0.020624, 0.463206, 0.154930, math.pi/2, 0.0, 0.0])
            self.linear_motion([-0.020624, 0.463206, 0.153530, math.pi/2, 0.0, 0.0])
            self.robot.open_gripper_set_width(0.03)
            self.linear_motion([-0.020624, 0.343206, 0.153530, math.pi/2, 0.0, 0.0])
            self.robot.move_robot_j([1.4881990556382296, -0.27014112220162356, -0.302704863314043, -2.8776053633846366, -0.031542427606052824, 2.6290648468607207, 0.8677514171226973])
            self.robot.move_robot_j([1.468016429100319, -0.6195214572956688, -0.25878762768444263, -2.486408156379466, -0.1479623147115265, 1.8460040196842615, 0.9731311520106263])
            self.robot.move_robot_j([1.4717125713446595, -0.37874429431296225, -0.19175355840565864, -1.454695109783511, -0.01441550570495835, 0.9970114136801825, 0.9801651583413957])
            self.robot.move_robot_j([1.4717125713446595, -0.37874429431296225, -0.19175355840565864, -1.454695109783511, -0.01441550570495835, 0.9970114136801825, 0.9801651583413957])
            self.robot.move_robot_j([0.054950104805828084, -0.39668647256232137, 0.06981596600127644, -1.1822355154380544, -0.028538222677169604, 0.6450058778382517, 0.8848990663066506])
            
            self._cartridge_in_quantos = cartridge_number
            
            self._logger.info(f"Cartridge now at position: {self._cartridge_in_quantos} now in Quantos")
           
            return 
        except:
            self._logger.error("Cartridge not available.")
            exit()

    def remove_cartridge_from_quantos(self, cartridge_number = 1):
        """
        Removes the cartridge from quantos. It terminates the program if the front door of quantos is closed in order to avoid potential collisions. 
        
        :param cartridge_number: and integer between 1 and 10 wchis represent the number of the cartridge.
        """
        self.check_quantos_door_position()
        try:
            self._logger.info("Robot removing cartridge from quantos ... ")
            self.robot.move_robot_j([0.054950104805828084, -0.39668647256232137, 0.06981596600127644, -1.1822355154380544, -0.028538222677169604, 0.6450058778382517, 0.8848990663066506])
            self.robot.move_robot_j([1.4717125713446595, -0.37874429431296225, -0.19175355840565864, -1.454695109783511, -0.01441550570495835, 0.9970114136801825, 0.9801651583413957])
            self.robot.move_robot_j( [1.468016429100319, -0.6195214572956688, -0.25878762768444263, -2.486408156379466, -0.1479623147115265, 1.8460040196842615, 0.9731311520106263])
            self.robot.move_robot_j([1.4881990556382296, -0.27014112220162356, -0.302704863314043, -2.8776053633846366, -0.031542427606052824, 2.6290648468607207, 0.8677514171226973])
            self.linear_motion([-0.020624, 0.343206, 0.152730, math.pi/2, 0.0, 0.0])
            self.robot.open_gripper_set_width(0.03)
            self.linear_motion([-0.020624, 0.462206, 0.152730, math.pi/2, 0.0, 0.0])
            self.robot.gripper.clamp()
            self.linear_motion([-0.020624, 0.462206, 0.155430, math.pi/2, 0.0, 0.0])
            self.linear_motion([-0.020624, 0.445206, 0.155430, math.pi/2, 0.0, 0.0])
            self.linear_motion([-0.022624, 0.445206, 0.155430, math.pi/2, 0.0, 0.0])
            self.linear_motion([-0.022624, 0.445206, 0.149430, math.pi/2, 0.0, 0.0])
            ####
            self.robot.move_robot_j( [1.6896320291805316, 0.01244918198713608, -0.06258759492568845, -2.6080483697255454, -0.12033771546343165, 2.661281414525643, 0.9884846218600867])
            self.robot.move_robot_j([1.623493001904404, -0.09582463145187611, -0.16833146013466532, -2.747920169294928, -0.12130647404896713, 2.6593146539794073, 0.7788315169190367])
            self.robot.move_robot_j([1.380799593490466, -0.4352248667580561, -0.2281504641854476, -2.730614678848585, -0.12271172765617813, 2.31335698694653, 0.8155934429334268])
            self.robot.move_robot_j([1.6675251447777997, -1.0275887485136066, -0.09035444692320839, -2.5317370912708634, -0.1183671841157807, 1.5240614581647351, 0.9499086411967872])
            #####cartridge_1
            if cartridge_number==1:
                self.linear_motion([0.0, 0.1894, 0.697005, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.063, 0.1894, 0.697005, 3.1414, 0.0, 0.0])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([0.0, 0.1894, 0.697005, 3.1414, 0.0, 0.0]) 
            #####cartridge_2
            if cartridge_number==2:
                self.linear_motion([0.0, 0.1895, 0.623205, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.0595, 0.1895, 0.623205, 3.1414, 0.0, 0.0])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([0.0, 0.1895, 0.623205, 3.1414, 0.0, 0.0])
                #####cartridge_3
            if cartridge_number==3:
                self.linear_motion([0.0, 0.1895,0.551905, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.059, 0.1895,0.551905, 3.1414, 0.0, 0.0])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([0.0, 0.1895,0.551905, 3.1414, 0.0, 0.0])
                #####cartridge_4
            if cartridge_number==4:
                self.linear_motion([0.0, 0.1885,0.480905, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.059, 0.1885,0.480905, 3.1414, 0.0, 0.0])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([0.0, 0.1885,0.480905, 3.1414, 0.0, 0.0])
                #####cartridge_5
            if cartridge_number==5:
                self.linear_motion([0.0, 0.1885,0.408705, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.058, 0.1885,0.408705, 3.1414, 0.0, 0.0])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([0.0, 0.1885,0.408705, 3.1414, 0.0, 0.0])
                #####cartridge_6
            if cartridge_number==6:
                self.robot.move_robot_j([2.0314804343006063, -0.8796317648426315, -0.23187811356260063, -1.990060961003889, -0.17293480516202647, 1.1392572491433886, -0.40220213498517116])
                self.linear_motion([0.0, 0.2335, 0.696405, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.0605, 0.2335, 0.696405, 3.1414, 0.0, 0.0])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([0.0, 0.2335, 0.696405, 3.1414, 0.0, 0.0])
                #####cartridge_7
            if cartridge_number==7:
                self.robot.move_robot_j([2.0314804343006063, -0.8796317648426315, -0.23187811356260063, -1.990060961003889, -0.17293480516202647, 1.1392572491433886, -0.40220213498517116])
                self.linear_motion([0.0, 0.2355, 0.624905, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.058, 0.2355, 0.624905, 3.1414, 0.0, 0.0])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([0.0, 0.2355, 0.624905, 3.1414, 0.0, 0.0])
                #####cartridge_8
            if cartridge_number==8:
                self.robot.move_robot_j([2.0314804343006063, -0.8796317648426315, -0.23187811356260063, -1.990060961003889, -0.17293480516202647, 1.1392572491433886, -0.40220213498517116])
                self.linear_motion([0.0, 0.235, 0.552755, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.058, 0.235,0.552755, 3.1414, 0.0, 0.0])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([0.0, 0.235, 0.552755, 3.1414, 0.0, 0.0])
                #####cartridge_9
            if cartridge_number==9:
                self.robot.move_robot_j([1.7597064712424024, -1.0150658254460587, -0.13655849616156046, -2.501267640933656, -0.10392897756232154, 1.5046610459751797, -0.6003663301302327])
                self.linear_motion([0.0, 0.234, 0.481555, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.057, 0.234,0.481555, 3.1414, 0.0, 0.0])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([0.0, 0.234, 0.481555, 3.1414, 0.0, 0.0])
                #####cartridge_10
            if cartridge_number==10:
                self.robot.move_robot_j([1.7640758390316662, -1.0486817768163845, -0.1358106571690105, -2.685871888116416, -0.10418765199733691, 1.6489508273998108, -0.5514215974149779])
                self.linear_motion([0.0, 0.234, 0.409855, 3.1414, 0.0, 0.0])
                self.linear_motion([-0.057, 0.234,0.409855, 3.1414, 0.0, 0.0])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([0.0, 0.234, 0.409855, 3.1414, 0.0, 0.0])
            self.linear_motion([0.015165, 0.182399, 0.681205, 3.1414, 0.0, 0.0])
            self.robot.move_robot_j([1.8286558759668823, -0.8510085091675601, -0.1403388809725381, -1.8050143277519628, -0.03595990048183335, 0.9802799679167741, -0.6215820595326329])
            self.robot.move_robot_j([1.6407204749960649, -0.8904579096760666, -0.12368042052210422, -1.842811449837266, -0.008949056352705547, 0.9683798163202072, 0.7932483173135283])
            self.robot.move_robot_j([1.6350166825077042, -0.3914084763736055, -0.2136805891948834, -1.3643024899905856, -0.006134169170864666, 0.8799257986810473, 0.791025193176184])
            
            self._logger.info(f"Cartridge at position {self._cartridge_in_quantos} now removed" )
            self._cartridge_in_quantos = None
            return
        except:
            self._logger.error(f'Cartridge {cartridge_number} is not available.')
            exit()

	################### Vial Manipulation methods ######################################
    def vial_capper_to_ika(self,ika_slot=1):
        '''
        
        '''
        #self.robot.move_robot_j([-1.631004642562126, 0.28467839003864087, 0.4286281546751658, -2.2697788718374152, -0.1717695542342133, 2.482683498965369, 1.3954791999037066])
        #self.robot.move_robot_j([-1.6059555230467388, 0.29961175878591256, 0.40966219290934097, -2.2882557112375896, -0.28129480303982085, 2.5347412309148454, 1.4626395472064615])
        self.robot.move_robot_j([-1.5684631792026085, 0.34770166642714384, 0.42795830030774223, -2.1893241288378986, -0.20302263963551162, 2.5031534219847784, 1.9735260637574934])
        self.robot.move_robot_j([-1.5667437001445836, 0.33464824626536266, 0.39512410021246525, -2.2757827378657827, -0.24780863948891418, 2.599961003568437, 1.7159009337599078])
        self.robot.gripper.clamp()
        self.robot.move_robot_j([-1.5684631792026085, 0.34770166642714384, 0.42795830030774223, -2.1893241288378986, -0.20302263963551162, 2.5031534219847784, 1.9735260637574934])
        self.robot.move_robot_j([-1.6344769049452634, 0.1768828558891744, 0.44529702574759433, -2.2810296887812322, -0.16951573207353385, 2.4211902517768915, 1.3592710603544218])
        #self.robot.move_robot_j([-1.588050496302153, 0.23802719115331047, 0.4130570925273032, -2.2655216583118105, -0.28090555198589, 2.4344173424508835, 1.4987858605558673])
        #self.robot.move_robot_j([-1.589136447900504, -0.08009124733690691, 0.45393646842732716, -2.2618028237192256, 0.04403724707212665, 2.194333258948699, 1.271420738713609])
        self.robot.move_robot_j([-1.5880930238192676, -0.5781302808293178, 0.37144537852108234, -2.345866105398888, 0.1367536832925524, 1.7822089331414963, 1.1019700488167175])
        self.robot.move_robot_j([-1.7351949474435657, -1.180955665220294, 0.14509397850213226, -2.571729930543063, 0.06623638577273916, 1.3931682261890832, 0.7017415762121477])
        self.robot.move_robot_j([-1.759874905553229, -0.6764247191579719, 0.2556986531929781, -1.5075261749803028, 0.07029177997968157, 0.8591582140392726, 0.7754334529414771])
        self.robot.move_robot_j([1.5492889621634232, -0.5542586173091019, -0.20297696281315983, -1.420489975134414, -0.06660811346107058, 0.7777394136852687, 0.733804698007802])
        self.robot.move_robot_j([1.4590764963210017, -0.3678046862366173, -0.2696941103265997, -2.7311696465102444, -0.1572924031651551, 2.347920595116085, 0.47549712705500874])
        self.linear_motion([0.148, 0.344, 0.22, math.pi/2, 0.0, 0.0])
        ###above slot 1 ika
        if ika_slot==1:
            self.linear_motion([0.148, 0.344, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.148, 0.344, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.148, 0.344, 0.108, math.pi/2, 0.0, 0.0])
            self.robot.open_gripper_set_width(0.03)
            self.linear_motion([0.148, 0.344, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.14, 0.34, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.148, 0.344, 0.22, math.pi/2, 0.0, 0.0])
        ###above slot 4 ika
        if ika_slot==4:
            self.linear_motion([0.146, 0.310, 0.22, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.146, 0.310, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.146, 0.310, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.146, 0.310, 0.108, math.pi/2, 0.0, 0.0])
            self.robot.open_gripper_set_width(0.03)
            self.linear_motion([0.146, 0.310, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.146, 0.310, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.146, 0.310, 0.22, math.pi/2, 0.0, 0.0])
        ###above slot 7 ika
        if ika_slot==7:
            self.linear_motion([0.145, 0.278, 0.22, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.145, 0.278, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.145, 0.278, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.145, 0.278, 0.108, math.pi/2, 0.0, 0.0])
            self.robot.open_gripper_set_width(0.03)
            self.linear_motion([0.145, 0.278, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.145, 0.278, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.145, 0.278, 0.22, math.pi/2, 0.0, 0.0])
        ####ika slot 9
        if ika_slot==9:
            self.linear_motion([0.235, 0.273, 0.22, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.235, 0.273, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.235, 0.273, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.235, 0.273, 0.108, math.pi/2, 0.0, 0.0])
            self.robot.open_gripper_set_width(0.03)
            self.linear_motion([0.235, 0.273, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.235, 0.273, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.235, 0.273, 0.22, math.pi/2, 0.0, 0.0])
        #### ika slot 6
        if ika_slot==6:
            self.linear_motion([0.235, 0.3065, 0.22, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.235, 0.3065, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.235, 0.3065, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.235, 0.3065, 0.108, math.pi/2, 0.0, 0.0])
            self.robot.open_gripper_set_width(0.03)
            self.linear_motion([0.235, 0.3065, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.235, 0.3065, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.235, 0.3065, 0.22, math.pi/2, 0.0, 0.0])
        ###above slot 2 ika
        if ika_slot==2:
            self.linear_motion([0.193, 0.359, 0.22, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.193, 0.359, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.193, 0.359, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.193, 0.359, 0.108, math.pi/2, 0.0, 0.0])
            self.robot.open_gripper_set_width(0.03)
            self.linear_motion([0.193, 0.359, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.193, 0.359, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.193, 0.359, 0.22, math.pi/2, 0.0, 0.0])
        ###above slot 3 ika
        if ika_slot==3:
            self.robot.move_robot_j([1.229144522867757, -0.2276054212035856, -0.2702685516717807, -2.6262098842163732, -0.08914504645167846, 2.4024826297230186, 0.24604706308990712])
            self.linear_motion([0.238, 0.340, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.238, 0.340, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.238, 0.340, 0.108, math.pi/2, 0.0, 0.0])
            self.robot.open_gripper_set_width(0.03)
            self.linear_motion([0.238, 0.340, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.238, 0.340, 0.14, math.pi/2, 0.0, 0.0])
            self.robot.move_robot_j([1.229144522867757, -0.2276054212035856, -0.2702685516717807, -2.6262098842163732, -0.08914504645167846, 2.4024826297230186, 0.24604706308990712])
        ###above slot 5 ika        
        if ika_slot==5:
            self.linear_motion([0.193, 0.3255, 0.22, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.193, 0.3255, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.193, 0.3255, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.193, 0.3255, 0.108, math.pi/2, 0.0, 0.0])
            self.robot.open_gripper_set_width(0.03)
            self.linear_motion([0.193, 0.3255, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.193, 0.3255, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.193, 0.3255, 0.22, math.pi/2, 0.0, 0.0])
        ###above slot 8 ika
        if ika_slot==8:
            self.linear_motion([0.191, 0.292, 0.22, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.191, 0.292, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.191, 0.292, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.191, 0.292, 0.108, math.pi/2, 0.0, 0.0])
            self.robot.open_gripper_set_width(0.03)
            self.linear_motion([0.191, 0.292, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.191, 0.292, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.191, 0.292, 0.22, math.pi/2, 0.0, 0.0])
        if ika_slot==10:
            self.linear_motion([0.189, 0.2585, 0.22, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.189, 0.2585, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.189, 0.2585, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.189, 0.2585, 0.108, math.pi/2, 0.0, 0.0])
            self.robot.open_gripper_set_width(0.03)
            self.linear_motion([0.189, 0.2585, 0.117, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.189, 0.2585, 0.14, math.pi/2, 0.0, 0.0])
            self.linear_motion([0.189, 0.2585, 0.22, math.pi/2, 0.0, 0.0])
        ##returning to home
        #self.robot.move_robot_j([1.438259602831121, -0.12324632104536457, -0.2692658616953947, -2.795705357884375, -0.13904051625863798, 2.6679343693969, 0.5386535819545388])
        #self.robot.move_robot_j([1.3853694243012813, -0.6445677989658557, -0.2282886732816696, -2.5076456596311716, -0.17347363211362868, 1.8872272850122644, 0.4908269000227253])
        self.robot.move_robot_j([1.4590764963210017, -0.3678046862366173, -0.2696941103265997, -2.7311696465102444, -0.1572924031651551, 2.347920595116085, 0.47549712705500874])
        self.robot.move_robot_j([1.5492889621634232, -0.5542586173091019, -0.20297696281315983, -1.420489975134414, -0.06660811346107058, 0.7777394136852687, 0.733804698007802])
    def vial_pump_to_capper(self,to_home=True):    
        '''
        
        '''
        self.linear_motion([0.021236, -0.465330, 0.394236, -1.571787, 0.0, 0.0])
        self.robot.gripper.clamp()
        self.linear_motion([0.021236, -0.465330, 0.434236, -1.571787, 0.0, 0.0])
        self.robot.move_robot_j([-1.7136670180538245, -0.5689924604683757, 0.10537462299434762, -2.2986901622571443, 0.05726123642330354, 1.7045236183332284, 0.7697684820666909])
        self.robot.move_robot_j([-1.5371494567770707, -0.8286127007634791, 0.32445757481586696, -2.725710542377673, 0.2266123803324169, 1.8949780377811856, 0.9430858572489685])
        self.robot.move_robot_j([-1.557104405286019, -0.13233281780195513, 0.436899661101793, -2.4847547997943162, 0.03855509165591663, 2.3825743986235723, 1.1308030216072997])
        #self.robot.move_robot_j([])
        #self.robot.move_robot_j([])
        #self.robot.move_robot_j([])
        #self.robot.move_robot_j([-1.7434511746189032, -0.30624892114940766, 0.19484101154929712, -2.118301702708177, 0.06236463957693841, 1.8054099711842007, 0.7798532573547629])
        #self.robot.move_robot_j([-1.6909784942091555, -0.2595396553926301, 0.43057283601844515, -2.061603377961276, 0.0694774820274777, 1.8100709510339699, 1.072042746132835])
        #self.robot.move_robot_j([-1.6604464185614336, -0.1482172403888285, 0.4934075346874524, -2.3698480366489343, 0.06369039563669099, 2.2450472729470996, 1.179624890639691])
        #self.robot.move_robot_j([-1.6474544434128433, 0.0955002395594329, 0.4768271105163976, -2.419614062192014, -0.08921113154951907, 2.4903134943134324, 1.2940314740996903])
        self.robot.move_robot_j([-1.6309107643429097, 0.2406991912000892, 0.44632846840267143, -2.304063950277352, -0.157368533031808, 2.5017716337309945, 1.3200139085605669])
        #self.robot.move_robot_j([-1.6362446678061235, 0.2812291292474981, 0.439157401243395, -2.288910242115921, -0.25358857851889394, 2.520420757240719, 1.422063902752844])
        self.robot.move_robot_j([-1.5684631792026085, 0.34770166642714384, 0.42795830030774223, -2.1893241288378986, -0.20302263963551162, 2.5031534219847784, 1.9735260637574934])
        self.robot.move_robot_j([-1.5667437001445836, 0.33464824626536266, 0.39512410021246525, -2.2757827378657827, -0.24780863948891418, 2.599961003568437, 1.7159009337599078])
        self.robot.open_gripper()
        self.robot.move_robot_j([-1.5684631792026085, 0.34770166642714384, 0.42795830030774223, -2.1893241288378986, -0.20302263963551162, 2.5031534219847784, 1.9735260637574934])
        self.robot.move_robot_j([-1.6344769049452634, 0.1768828558891744, 0.44529702574759433, -2.2810296887812322, -0.16951573207353385, 2.4211902517768915, 1.3592710603544218])
        if to_home:
            self.robot.move_robot_j([-1.557104405286019, -0.13233281780195513, 0.436899661101793, -2.4847547997943162, 0.03855509165591663, 2.3825743986235723, 1.1308030216072997])
            self.robot.move_robot_j([-1.5371494567770707, -0.8286127007634791, 0.32445757481586696, -2.725710542377673, 0.2266123803324169, 1.8949780377811856, 0.9430858572489685])
            self.robot.move_robot_j([-1.7136670180538245, -0.5689924604683757, 0.10537462299434762, -2.2986901622571443, 0.05726123642330354, 1.7045236183332284, 0.7697684820666909])
            self.robot.move_robot_j([-1.759874905553229, -0.6764247191579719, 0.2556986531929781, -1.5075261749803028, 0.07029177997968157, 0.8591582140392726, 0.7754334529414771]) 
            self.robot.move_robot_j([-0.052387438984816535, -0.5442788602176466, 0.03260193974825373, -1.4529518636099459, 0.024215675451689296, 0.756491325802273, 0.8650050505176187])
    
    def vial_capper_to_pump(self):
        '''
        
        '''
        ## moving from home to the capper TODO
        #self.robot.move_robot_j([1.4590764963210017, -0.3678046862366173, -0.2696941103265997, -2.7311696465102444, -0.1572924031651551, 2.347920595116085, 0.47549712705500874])
        #self.robot.move_robot_j([1.5492889621634232, -0.5542586173091019, -0.20297696281315983, -1.420489975134414, -0.06660811346107058, 0.7777394136852687, 0.733804698007802])
        self.robot.move_robot_j([-1.759874905553229, -0.6764247191579719, 0.2556986531929781, -1.5075261749803028, 0.07029177997968157, 0.8591582140392726, 0.7754334529414771])
        self.robot.move_robot_j([-1.7351949474435657, -1.180955665220294, 0.14509397850213226, -2.571729930543063, 0.06623638577273916, 1.3931682261890832, 0.7017415762121477])
        self.robot.move_robot_j([-1.5880930238192676, -0.5781302808293178, 0.37144537852108234, -2.345866105398888, 0.1367536832925524, 1.7822089331414963, 1.1019700488167175])
        self.robot.move_robot_j([-1.589136447900504, -0.08009124733690691, 0.45393646842732716, -2.2618028237192256, 0.04403724707212665, 2.194333258948699, 1.271420738713609])
        self.robot.move_robot_j([-1.588050496302153, 0.23802719115331047, 0.4130570925273032, -2.2655216583118105, -0.28090555198589, 2.4344173424508835, 1.4987858605558673])
        #self.robot.move_robot_j([-1.6059555230467388, 0.29961175878591256, 0.40966219290934097, -2.2882557112375896, -0.28129480303982085, 2.5347412309148454, 1.4626395472064615])
        #input("3")
        self.robot.move_robot_j([-1.5684631792026085, 0.34770166642714384, 0.42795830030774223, -2.1893241288378986, -0.20302263963551162, 2.5031534219847784, 1.9735260637574934])
        self.robot.move_robot_j([-1.5667437001445836, 0.33464824626536266, 0.39512410021246525, -2.2757827378657827, -0.24780863948891418, 2.599961003568437, 1.7159009337599078])
        self.robot.gripper.clamp()
        self.robot.move_robot_j([-1.5667437001445836, 0.33464824626536266, 0.39512410021246525, -2.2757827378657827, -0.24780863948891418, 2.599961003568437, 1.7159009337599078])
        self.robot.move_robot_j([-1.5684631792026085, 0.34770166642714384, 0.42795830030774223, -2.1893241288378986, -0.20302263963551162, 2.5031534219847784, 1.9735260637574934])
        #self.robot.move_robot_j([-1.6403582514545372, 0.30725608892031353, 0.43641001606682794, -2.2875380253274535, -0.25359014151131926, 2.5353142922189496, 1.4220420811714016])
        #self.robot.move_robot_j([-1.6362446678061235, 0.2812291292474981, 0.439157401243395, -2.288910242115921, -0.25358857851889394, 2.520420757240719, 1.422063902752844])
        self.robot.move_robot_j([-1.6385354666077911, 0.2752530936525579, 0.4484024262835129, -2.290046701732434, -0.159073760220551, 2.5323927586343555, 1.3208766644728673])
        self.robot.move_robot_j([-1.8042963885452152, -0.8104631285918386, 0.7506233098622437, -2.6818241853663936, 0.45941034520506363, 2.00530636400654, 0.9124445720584017])
        self.robot.move_robot_j([-1.8673497444591318, -0.8604081446481199, 0.23389602297525025, -2.4771717399926976, 0.17391716161039142, 1.5993189661767746, 0.7278961102341611])
        self.robot.move_robot_j([-1.8714251921637015, -0.3732063998688628, 0.2661084838038997, -2.1345591327265683, 0.13079034563347144, 1.7676654745207891, 0.735445656750812])
        #self.robot.move_robot_j([-1.6474544434128433, 0.0955002395594329, 0.4768271105163976, -2.419614062192014, -0.08921113154951907, 2.4903134943134324, 1.2940314740996903])
        #self.robot.move_robot_j([-1.6604464185614336, -0.1482172403888285, 0.4934075346874524, -2.3698480366489343, 0.06369039563669099, 2.2450472729470996, 1.179624890639691])
        #self.robot.move_robot_j([-1.6909784942091555, -0.2595396553926301, 0.43057283601844515, -2.061603377961276, 0.0694774820274777, 1.8100709510339699, 1.072042746132835])
        #input()
        self.robot.move_robot_j([-1.7434511746189032, -0.30624892114940766, 0.19484101154929712, -2.118301702708177, 0.06236463957693841, 1.8054099711842007, 0.7798532573547629])
        #input()
        self.linear_motion([0.021236, -0.465330, 0.434236, -1.571787, 0.0, 0.0])
        self.linear_motion([0.021236, -0.465330, 0.394236, -1.571787, 0.0, 0.0])
        self.robot.open_gripper_set_width(0.03)
        #self.robot.move_robot_j([-1.7018724064408683, -0.6934047432546074, 0.2276472941156037, -1.554785427316593, 0.054903464623532364, 0.8587326710877167, 0.7673473637652249])
    def vial_capper_to_rack(self, rack_number=1):
        '''
        
        '''
        self.vial_capper_to_pump()
        self.vial_pump_to_rack(vial_number=rack_number)

    def vial_rack_to_pump(self, vial_number=1):
        """
        Moves a vial from the rack to the pump.
        :param vial_number: an integer which possible values go from 1 to 16 
        """
        try:
            self.robot.move_robot_j([-0.13743377816351218, -0.5749181416624936, 0.0819944231651873, -1.49696418198368, -0.008074455948339568, 0.8040668631659613, 0.7686585235761272])
            self.robot.move_robot_j([-1.743650449039492, -0.7486180810175443, 0.22241080045281791, -1.5211490588941072, 0.005688086230194893, 0.7976024832725525, 0.6795741435431754])   
            self.robot.move_robot_j([-1.7285189013062858, -1.2744280272868642, 0.18960489550808016, -2.6532256667884626, 0.1529083159873238, 1.3535750827259487, 0.6962508853450418])
            self.robot.move_robot_j([-1.9410520033418084, -1.3629693503796398, 0.10535519492312481, -2.676664989002964, 0.1223482074176301, 1.3162604484028286, 2.0521033040848042]) 
            ##Home to rack
            #Rack 1
            if vial_number==1:
                self.linear_motion([-0.013, -0.151, 0.444198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.073, -0.151, 0.444198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.073, -0.151, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.151, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.151, 0.444198, 3.128527, 0.015399, 0.004588])
            #Rack 2
            if vial_number==2:         
                self.linear_motion([-0.013, -0.203, 0.444198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.073, -0.203, 0.444198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.073, -0.203, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.203, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.203, 0.444198, 3.128527, 0.015399, 0.004588])
            #Rack 3
            if vial_number==3: 
                self.linear_motion([-0.013, -0.251, 0.444198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.073, -0.251, 0.444198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.073, -0.251, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.251, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.251, 0.444198, 3.128527, 0.015399, 0.004588])
            #Rack 4
            if vial_number==4: 
                self.linear_motion([-0.013, -0.302, 0.444198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.073, -0.302, 0.444198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.073, -0.302, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.302, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.302, 0.444198, 3.128527, 0.015399, 0.004588])
            #Rack 5
            if vial_number==5: 
                self.linear_motion([-0.013, -0.351, 0.444198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.073, -0.351, 0.444198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.073, -0.351, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.351, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.351, 0.444198, 3.128527, 0.015399, 0.004588])
            #Rack 6
            if vial_number==6: 
                self.linear_motion([-0.013, -0.403, 0.444198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.0745, -0.403, 0.444198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.0745, -0.403, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.403, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.403, 0.444198, 3.128527, 0.015399, 0.004588])
            #Rack 7
            if vial_number==7: 
                self.linear_motion([-0.013, -0.453, 0.444198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.075, -0.453, 0.444198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.075, -0.453, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.453, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.453, 0.444198, 3.128527, 0.015399, 0.004588])
            #Rack
            if vial_number==8: 
                self.linear_motion([-0.013, -0.503, 0.444198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.077, -0.503, 0.444198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.077, -0.503, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.503, 0.464198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.503, 0.444198, 3.128527, 0.015399, 0.004588])
            #Rack 9
            if vial_number==9:
                self.linear_motion([-0.013, -0.149, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.112, -0.149, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.112, -0.149, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.149, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.149, 0.517198, 3.128527, 0.015399, 0.004588])
            #Rack 10
            if vial_number==10:         
                self.linear_motion([-0.013, -0.200, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.114, -0.200, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.114, -0.200, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.200, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.200, 0.517198, 3.128527, 0.015399, 0.004588])
            #Rack 11 
            if vial_number==11: 
                self.linear_motion([-0.013, -0.251, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.114, -0.251, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.114, -0.251, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.251, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.251, 0.517198, 3.128527, 0.015399, 0.004588])
            #Rack 12 
            if vial_number==12: 
                self.linear_motion([-0.013, -0.301, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.114, -0.301, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.114, -0.301, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.301, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.301, 0.517198, 3.128527, 0.015399, 0.004588])
            #Rack 13 
            if vial_number==13: 
                self.linear_motion([-0.013, -0.348, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.115, -0.348, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.115, -0.348, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.348, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.348, 0.517198, 3.128527, 0.015399, 0.004588])
            #Rack 14 
            if vial_number==14: 
                self.linear_motion([-0.013, -0.400, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.117, -0.400, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.117, -0.400, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.400, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.400, 0.517198, 3.128527, 0.015399, 0.004588])
            #Rack 15 
            if vial_number==15: 
                self.linear_motion([-0.013, -0.451, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.117, -0.451, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.117, -0.451, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.451, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.451, 0.517198, 3.128527, 0.015399, 0.004588])
            #Rack 16 
            if vial_number==16: 
                self.linear_motion([-0.013, -0.502, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.1175, -0.502, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.gripper.clamp()
                self.linear_motion([-0.1175, -0.502, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.502, 0.537198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.502, 0.517198, 3.128527, 0.015399, 0.004588])
            ###placing
            self.robot.move_robot_j([-1.7125169298272385, -0.9589622717991378, 0.22067854790161406, -2.60667933711671, 0.12227936733431286, 1.6349339764383102, 0.8318518518476216])
            self.robot.move_robot_j([-1.7459924050548619, -0.6597527398045244, 0.1841714407644774, -2.3162459762974787, 0.07382472326404896, 1.658117745740659, 0.8202390908916841])
            self.robot.move_robot_j([-1.749480187366384, -0.29367109431908056, 0.19448403653483382, -2.1096611268365324, 0.06114327257563501, 1.7995932398619674, 0.7559862168803811])
            self.robot.move_robot_j([-1.750921373616417, -0.28819621214300506, 0.19862928508042696, -2.1684026530545992, 0.06158574515249994, 1.8673437302377487, 0.7740015745337558])
            self.robot.move_robot_j([-1.7496210484086416, -0.27930905445416765, 0.19761741688988496, -2.171783759620725, 0.06241802596383625, 1.8665404551294116, 0.7710181514596273])
            self.robot.open_gripper()       
        except:
            self._logger.error(f'Vial {vial_number} not available.')
            #exit()


    def vial_rack_to_ika(self, vial_number=1, ika_slot_number=1):
        """
        Moves a vial from the rack to the IKA station.
        :param vial_number: an integer which possible values go from 1 to 22 
        :param ika_slot_number: an integer which possible values go from 1 to 12
        """
        try:
            self.vial_rack_to_pump(vial_number=vial_number)
            self.vial_pump_to_capper(to_home=False) #TODO get rid of this step
            self.vial_capper_to_ika(ika_slot=vial_number)

            return
        except:
            self._logger.error(f'Vial {vial_number} or IKA slot {ika_slot_number} not available.')
            #self.camera.stop_streaming() #TODO fix
            exit()

    def vial_rack_to_quantos(self, vial_number=1):
        """
        Moves a vial from the rack to the quantos mettler. 
        Terminates the program if the front door of the quantos station is closed. 
        :param vial_number: an integer which possible values go from 1 to 22. 
        """
        self.check_quantos_door_position()
        self.vial_rack_to_pump(vial_number=vial_number)
        self.vial_pump_to_quantos()
        return
    
    def vial_ika_to_rack(self, ika_slot=1):
        """
        Moves a vial from the ika station to the rack.
        :param vial_number: an integer which possible values go from 1 to 22 
        :param ika_slot_number: an integer which possible values go from 1 to 12
        """
        self.vial_ika_to_pump(ika_slot=ika_slot)
        self.vial_pump_to_rack(vial_number=ika_slot)
        return
    
    def vial_ika_to_quantos(self, ika_slot_number=1):
        """
        Moves a vial from the IKA station to the quantos station.
        Terminates if the front door of the quantos station is closed in order to avoid potential collisions.
        :param ika_slot_number: an integer which possible values go from 1 to 12
        """
        self.check_quantos_door_position()
        self.vial_ika_to_pump(ika_slot_number=ika_slot_number)
        self.vial_pump_to_quantos()
        return
    def vial_pump_to_rack(self, vial_number=1):
        """
        Moves a vial from the vial holder of the pump to the rack.
        :param vial_number: an integer which possible values go from 1 to 22 
        :param from_home: bool when set to True, the robot executes this method from its home position. When is set to False, the robot executes its movements from a position close to the pump.
        """
        try:
             
            ##start
            #self.robot.gripper.clamp()
            self.robot.move_robot_j([-1.7496210484086416, -0.27930905445416765, 0.19761741688988496, -2.171783759620725, 0.06241802596383625, 1.8665404551294116, 0.7710181514596273])
            self.robot.gripper.clamp()
            self.robot.move_robot_j([-1.750921373616417, -0.28819621214300506, 0.19862928508042696, -2.1684026530545992, 0.06158574515249994, 1.8673437302377487, 0.7740015745337558])
            self.robot.move_robot_j([-1.749480187366384, -0.29367109431908056, 0.19448403653483382, -2.1096611268365324, 0.06114327257563501, 1.7995932398619674, 0.7559862168803811])
            self.robot.move_robot_j([-1.7459924050548619, -0.6597527398045244, 0.1841714407644774, -2.3162459762974787, 0.07382472326404896, 1.658117745740659, 0.8202390908916841])
            self.robot.move_robot_j([-1.7125169298272385, -0.9589622717991378, 0.22067854790161406, -2.60667933711671, 0.12227936733431286, 1.6349339764383102, 0.8318518518476216])
            self.robot.move_robot_j([-1.834956466708267, -1.262718312179833, 0.07695800682013496, -2.5448007061955655, 0.09362280228402879, 1.2683053020824353, 2.280488008309181])
            ##vials###
            #Rack 16
            if vial_number==16:        
                self.linear_motion([-0.013, -0.502, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.502, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.1175, -0.502, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.1175, -0.502, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.502, 0.517198, 3.128527, 0.015399, 0.004588])    
            #Rack 15
            if vial_number==15:        
                self.linear_motion([-0.013, -0.451, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.451, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.117, -0.451, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.117, -0.451, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.451, 0.517198, 3.128527, 0.015399, 0.004588]) 
            #Rack 14
            if vial_number==14:        
                self.linear_motion([-0.013, -0.400, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.400, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.117, -0.400, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.117, -0.400, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.400, 0.517198, 3.128527, 0.015399, 0.004588]) 
            #Rack 13
            if vial_number==13:        
                self.linear_motion([-0.013, -0.348, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.348, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.115, -0.348, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.115, -0.348, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.348, 0.517198, 3.128527, 0.015399, 0.004588]) 
            #Rack 12
            if vial_number==12:        
                self.linear_motion([-0.013, -0.301, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.301, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.114, -0.301, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.114, -0.301, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.301, 0.517198, 3.128527, 0.015399, 0.004588]) 
            #Rack 11
            if vial_number==11:        
                self.linear_motion([-0.013, -0.251, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.251, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.114, -0.251, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.114, -0.251, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.251, 0.517198, 3.128527, 0.015399, 0.004588]) 
            #Rack 10
            if vial_number==10:        
                self.linear_motion([-0.013, -0.200, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.200, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.114, -0.200, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.114, -0.200, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.200, 0.517198, 3.128527, 0.015399, 0.004588])           
            ######Rack 9
            if vial_number==9:
                self.linear_motion([-0.013, -0.149, 0.517198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.149, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.112, -0.149, 0.539198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.112, -0.149, 0.517198, 3.128527, 0.015399, 0.004588])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.149, 0.517198, 3.128527, 0.015399, 0.004588])
            #Rack
            if vial_number==8: 
                self.linear_motion([-0.013, -0.503, 0.444198, 3.128527, 0.015399, 0.004588]) 
                self.linear_motion([-0.013, -0.503, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.077, -0.503, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.077, -0.503, 0.444198, 3.128527, 0.015399, 0.004588])  
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.503, 0.444198, 3.128527, 0.015399, 0.004588])
            #Rack 7
            if vial_number==7: 
                self.linear_motion([-0.013, -0.452, 0.444198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.452, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.0745, -0.452, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.0745, -0.452, 0.444198, 3.128527, 0.015399, 0.004588])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.452, 0.444198, 3.128527, 0.015399, 0.004588])
            #Rack 6
            if vial_number==6:
                self.linear_motion([-0.013, -0.401, 0.444198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.401, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.074, -0.401, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.074, -0.401, 0.444198, 3.128527, 0.015399, 0.004588])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.401, 0.444198, 3.128527, 0.015399, 0.004588])
            #Rack 5
            if vial_number==5: 
                self.linear_motion([-0.013, -0.351, 0.444198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.351, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.073, -0.351, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.073, -0.351, 0.444198, 3.128527, 0.015399, 0.004588])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.351, 0.444198, 3.128527, 0.015399, 0.004588])
            #Rack 4
            if vial_number==4: 
                self.linear_motion([-0.013, -0.302, 0.444198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.302, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.073, -0.302, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.073, -0.302, 0.444198, 3.128527, 0.015399, 0.004588])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.302, 0.444198, 3.128527, 0.015399, 0.004588])
            #Rack 3
            if vial_number==3: 
                self.linear_motion([-0.013, -0.252, 0.444198, 3.128527, 0.015399, 0.004588]) 
                self.linear_motion([-0.013, -0.252, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.073, -0.252, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.073, -0.252, 0.444198, 3.128527, 0.015399, 0.004588])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.252, 0.444198, 3.128527, 0.015399, 0.004588])
            #Rack 2
            if vial_number==2:     
                self.linear_motion([-0.013, -0.203, 0.444198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.203, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.073, -0.203, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.073, -0.203, 0.444198, 3.128527, 0.015399, 0.004588])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.203, 0.444198, 3.128527, 0.015399, 0.004588])
            #Rack 1
            if vial_number==1:
                self.linear_motion([-0.013, -0.151, 0.444198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.013, -0.151, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.073, -0.151, 0.466198, 3.128527, 0.015399, 0.004588])
                self.linear_motion([-0.073, -0.151, 0.444198, 3.128527, 0.015399, 0.004588])
                self.robot.open_gripper_set_width(0.03)
                self.linear_motion([-0.013, -0.151, 0.444198, 3.128527, 0.015399, 0.004588])
            ##end
            self.robot.move_robot_j([-1.9410520033418084, -1.3629693503796398, 0.10535519492312481, -2.676664989002964, 0.1223482074176301, 1.3162604484028286, 2.0521033040848042])
            self.robot.move_robot_j([-1.7285189013062858, -1.2744280272868642, 0.18960489550808016, -2.6532256667884626, 0.1529083159873238, 1.3535750827259487, 0.6962508853450418])
            self.robot.move_robot_j([-1.743650449039492, -0.7486180810175443, 0.22241080045281791, -1.5211490588941072, 0.005688086230194893, 0.7976024832725525, 0.6795741435431754])   
            self.robot.move_robot_j([-0.13743377816351218, -0.5749181416624936, 0.0819944231651873, -1.49696418198368, -0.008074455948339568, 0.8040668631659613, 0.7686585235761272])            
            ###
        except:
            self._logger.error(f'Vial {vial_number} not available.')
            self.camera.stop_streaming()
            exit()

    
    def vial_ika_to_pump(self, ika_slot=1):
        """
        Moves a vial from the IKA station to the vial holder of the pump.
        :param ika_slot: an integer which possible values go from 1 to 10
        """
        try:
            self.robot.open_gripper_set_width(0.03)
            self.robot.move_robot_j([1.5492889621634232, -0.5542586173091019, -0.20297696281315983, -1.420489975134414, -0.06660811346107058, 0.7777394136852687, 0.733804698007802])    
            self.robot.move_robot_j([1.4590764963210017, -0.3678046862366173, -0.2696941103265997, -2.7311696465102444, -0.1572924031651551, 2.347920595116085, 0.47549712705500874])
        ###above slot 1 ika
            if ika_slot==10:
                self.linear_motion([0.189, 0.2585, 0.22, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.189, 0.2585, 0.14, math.pi/2, 0.0, 0.0]) 
                self.linear_motion([0.189, 0.2585, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.189, 0.2585, 0.108, math.pi/2, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([0.189, 0.2585, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.189, 0.2585, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.189, 0.2585, 0.22, math.pi/2, 0.0, 0.0])
            ####ika slot 9
            if ika_slot==9:
                self.linear_motion([0.235, 0.273, 0.22, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.235, 0.273, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.235, 0.273, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.235, 0.273, 0.108, math.pi/2, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([0.235, 0.273, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.235, 0.273, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.235, 0.273, 0.22, math.pi/2, 0.0, 0.0])
            ###above slot 8 ika
            if ika_slot==8:
                self.linear_motion([0.191, 0.292, 0.22, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.191, 0.292, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.191, 0.292, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.191, 0.292, 0.108, math.pi/2, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([0.191, 0.292, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.191, 0.292, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.191, 0.292, 0.22, math.pi/2, 0.0, 0.0])
            ###above slot 7 ika
            if ika_slot==7:
                self.linear_motion([0.145, 0.278, 0.22, math.pi/2, 0.0, 0.0]) 
                self.linear_motion([0.145, 0.278, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.145, 0.278, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.145, 0.278, 0.108, math.pi/2, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([0.145, 0.278, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.145, 0.278, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.145, 0.278, 0.22, math.pi/2, 0.0, 0.0])
            #### ika slot 6
            if ika_slot==6:
                self.linear_motion([0.235, 0.3065, 0.22, math.pi/2, 0.0, 0.0]) 
                self.linear_motion([0.235, 0.3065, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.235, 0.3065, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.235, 0.3065, 0.108, math.pi/2, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([0.235, 0.3065, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.235, 0.3065, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.235, 0.3065, 0.22, math.pi/2, 0.0, 0.0])
            ###above slot 5 ika        
            if ika_slot==5:
                self.linear_motion([0.193, 0.3255, 0.22, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.193, 0.3255, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.193, 0.3255, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.193, 0.3255, 0.108, math.pi/2, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([0.193, 0.3255, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.193, 0.3255, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.193, 0.3255, 0.22, math.pi/2, 0.0, 0.0])
            ###above slot 4 ika
            if ika_slot==4:
                self.linear_motion([0.146, 0.310, 0.22, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.146, 0.310, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.146, 0.310, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.146, 0.310, 0.108, math.pi/2, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([0.146, 0.310, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.146, 0.310, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.146, 0.310, 0.22, math.pi/2, 0.0, 0.0])
            ###above slot 3 ika
            if ika_slot==3:
                self.robot.move_robot_j([1.229144522867757, -0.2276054212035856, -0.2702685516717807, -2.6262098842163732, -0.08914504645167846, 2.4024826297230186, 0.24604706308990712]) 
                self.robot.move_robot_j([1.2276909838894436, -0.026947655328010255, -0.2702575307155834, -2.6803075786724424, -0.0160901819860408, 2.6531646594471403, 0.1863803567806512])
                self.robot.move_robot_j([1.2357093439909963, 0.04515318062603092, -0.27001008293777884, -2.6817974331169796, 0.028857123146899772, 2.7236437854237026, 0.15409815305230973])
                self.robot.move_robot_j([1.2399981366375037, 0.07434085780277597, -0.26990263710735446, -2.6808501467210526, 0.05119902942692767, 2.7505977432992723, 0.1381451022789547])
                self.robot.gripper.clamp()
                self.robot.move_robot_j([1.2357093439909963, 0.04515318062603092, -0.27001008293777884, -2.6817974331169796, 0.028857123146899772, 2.7236437854237026, 0.15409815305230973])
                self.robot.move_robot_j([1.2276909838894436, -0.026947655328010255, -0.2702575307155834, -2.6803075786724424, -0.0160901819860408, 2.6531646594471403, 0.1863803567806512])
                self.robot.move_robot_j([1.229144522867757, -0.2276054212035856, -0.2702685516717807, -2.6262098842163732, -0.08914504645167846, 2.4024826297230186, 0.24604706308990712])
            ###above slot 2 ika
            if ika_slot==2:
                self.linear_motion([0.193, 0.359, 0.22, math.pi/2, 0.0, 0.0]) 
                self.linear_motion([0.193, 0.359, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.193, 0.359, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.193, 0.359, 0.108, math.pi/2, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([0.193, 0.359, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.193, 0.359, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.193, 0.359, 0.22, math.pi/2, 0.0, 0.0])                               
            if ika_slot==1:
                self.linear_motion([0.148, 0.344, 0.22, math.pi/2, 0.0, 0.0]) 
                self.linear_motion([0.14, 0.34, 0.14, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.148, 0.344, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.148, 0.344, 0.108, math.pi/2, 0.0, 0.0])
                self.robot.gripper.clamp()
                self.linear_motion([0.148, 0.344, 0.117, math.pi/2, 0.0, 0.0])
                self.linear_motion([0.148, 0.344, 0.14, math.pi/2, 0.0, 0.0])
            #self.linear_motion([0.148, 0.344, 0.22, math.pi/2, 0.0, 0.0]) #TODO change
            self.robot.move_robot_j([1.417212652725086, -0.3701414478774185, -0.2697282641770565, -2.7568747279183903, -0.14130196021942054, 2.3940143196847705, 0.48386919909351966])
            #input('aqui')
            ####
            self.robot.move_robot_j([1.4590764963210017, -0.3678046862366173, -0.2696941103265997, -2.7311696465102444, -0.1572924031651551, 2.347920595116085, 0.47549712705500874])
            self.robot.move_robot_j([1.5492889621634232, -0.5542586173091019, -0.20297696281315983, -1.420489975134414, -0.06660811346107058, 0.7777394136852687, 0.733804698007802])
            self.robot.move_robot_j([-1.759874905553229, -0.6764247191579719, 0.2556986531929781, -1.5075261749803028, 0.07029177997968157, 0.8591582140392726, 0.7754334529414771])

            self.robot.move_robot_j([-1.7125169298272385, -0.9589622717991378, 0.22067854790161406, -2.60667933711671, 0.12227936733431286, 1.6349339764383102, 0.8318518518476216])
            self.robot.move_robot_j([-1.7459924050548619, -0.6597527398045244, 0.1841714407644774, -2.3162459762974787, 0.07382472326404896, 1.658117745740659, 0.8202390908916841])
            self.robot.move_robot_j([-1.749480187366384, -0.29367109431908056, 0.19448403653483382, -2.1096611268365324, 0.06114327257563501, 1.7995932398619674, 0.7559862168803811])
            self.robot.move_robot_j([-1.750921373616417, -0.28819621214300506, 0.19862928508042696, -2.1684026530545992, 0.06158574515249994, 1.8673437302377487, 0.7740015745337558])
            self.robot.move_robot_j([-1.7496210484086416, -0.27930905445416765, 0.19761741688988496, -2.171783759620725, 0.06241802596383625, 1.8665404551294116, 0.7710181514596273])
            ####
            self.robot.open_gripper()  
            return
        except:
            self._logger.error(f'IKA slot {ika_slot} not available.')
            self.camera.stop_streaming()
            exit()
    
    def vial_quantos_to_ika(self,ika_slot_number=1):
        """
        Moves a vial from the quantos station to the IKA station.
        :param ika_slot_number: an integer which possible values go from 1 to 12
        """
        self.check_quantos_door_position()
        self.vial_quantos_to_pump()
        self.vial_pump_to_ika(ika_slot_number=ika_slot_number)
        return
    
    def vial_quantos_to_rack(self,vial_number=1):
        """
        Moves a vial from the quantos station to the rack.
        Terminates if the front door of the quantos station is closed in order to avoid potential collisions.
        :param vial_number: an integer which possible values go from 1 to 22 
        """
        self.check_quantos_door_position()
        self.vial_quantos_to_pump()    
        self.vial_pump_to_rack(vial_number=vial_number)
        return
    
    def vial_pump_to_quantos(self):
        """
        Moves a vial from the vial holder of the pump to the Quantos mettler station. 
        Terminates the program if the front door of the quantos station is closed to avoid potential collisions. 
        """
        try:
            self.check_quantos_door_position()
            self.linear_motion([0.021236, -0.465330, 0.394236, -1.571787, 0.0, 0.0])
            self.robot.gripper.clamp()
            self.linear_motion([0.021236, -0.465330, 0.434236, -1.571787, 0.0, 0.0])
            self.linear_motion([0.021236, -0.265330, 0.434236, -1.571787, 0.0, 0.0])
            self.linear_motion([0.021236, -0.265330, 0.734236, -1.571787, 0.0, 0.0])
            self.robot.move_robot_j([-0.49146811520560546, -0.5483666040604575, 0.008699827790391025, -1.424562310637089, -0.1584492087530014, 0.9070381476330659, 0.6617912204484846])
            self.robot.move_robot_j([0.863253819507465, -0.5490223970580519, -0.060526590153836365, -1.505593206711674, -0.023240255180332396, 0.8139228273497687, 1.0326294075855897])
            self.robot.move_robot_j([1.5437224203633981, -0.8535716153432693, -0.02090855556648028, -2.3220350435825816, -0.030267629832360667, 1.4690346631473965, 0.7142224947785337])
            self.linear_motion([0.020783, 0.277155, 0.513770, math.pi/2, 0.0, 0.0])
            self.robot.move_robot_j([1.6131610135697478, -0.853325663533127, -0.05353319992935447, -2.69698212503132, -0.09767679642968707, 1.8604011267523237, 0.8483259122309667])
            self.robot.move_robot_j( [1.6149535670902366, -0.30035995266730325, -0.09664097981222683, -2.7755572217900024, -0.09452590536408127, 2.496923201190101, 0.8401453860774636])
            self.robot.move_robot_j([1.628786448913708, 0.07672654361264745, -0.092344672147254, -2.68894268090585, -0.023956333485348303, 2.7958885248242646, 0.2166834870786398])
            self.robot.move_robot_j([1.6339519956488358, 0.20316569954888863, -0.01437163186073303, -2.527209927679671, -0.016769896860926475, 2.70550021408811, 0.8611653534736896])
            self.linear_motion([-0.021548, 0.455917, 0.094333, math.pi/2, 0.0, 0.0])
            self.linear_motion([-0.018376, 0.475474, 0.089415, 1.570832, 0.001657, -0.000339])
            self.robot.open_gripper_set_width(0.035)
            self.linear_motion([-0.018376, 0.325474, 0.089415, 1.570832, 0.001657, -0.000339])
            self.robot.move_robot_j([1.612750472587451, -0.9394352493369788, -0.1741023376255535, -2.94717707379659, -0.10549786026286026, 1.9851371329095377, 0.7427021295096015])
            self.robot.move_robot_j([1.643955648388779, -0.7035506518127264, -0.11034566835980666, -1.699107937695687, -0.03175135499520129, 0.9279511667357548, 0.7056178085434384])
            return
        except:
            self._logger.error(f'Robot not available, terminating program...')
            self.camera.stop_streaming()
            exit()


    def vial_quantos_to_pump(self):
        """
        Moves a vial from the quantos station to the vial holder of the pump.
        Terminates if the front door of the quantos station is closed in order to avoid potential collisions.
        """
        try:
            self.check_quantos_door_position() 
            self.robot.move_robot_j([1.612750472587451, -0.9394352493369788, -0.1741023376255535, -2.94717707379659, -0.10549786026286026, 1.9851371329095377, 0.7427021295096015])
            self.linear_motion([-0.018376, 0.325474, 0.089415, 1.570832, 0.001657, -0.000339])
            self.linear_motion([-0.018376, 0.475474, 0.089415, 1.570832, 0.001657, -0.000339])
            self.robot.gripper.clamp()
            self.linear_motion([-0.021548, 0.455917, 0.094333, math.pi/2, 0.0, 0.0])
            self.robot.move_robot_j([1.6339519956488358, 0.20316569954888863, -0.01437163186073303, -2.527209927679671, -0.016769896860926475, 2.70550021408811, 0.8611653534736896])
            self.robot.move_robot_j([1.628786448913708, 0.07672654361264745, -0.092344672147254, -2.68894268090585, -0.023956333485348303, 2.7958885248242646, 0.2166834870786398])
            self.robot.move_robot_j( [1.6149535670902366, -0.30035995266730325, -0.09664097981222683, -2.7755572217900024, -0.09452590536408127, 2.496923201190101, 0.8401453860774636])
            self.robot.move_robot_j([1.6131610135697478, -0.853325663533127, -0.05353319992935447, -2.69698212503132, -0.09767679642968707, 1.8604011267523237, 0.8483259122309667])
            self.linear_motion([0.020783, 0.277155, 0.513770, math.pi/2, 0.0, 0.0])
            self.robot.move_robot_j([1.5437224203633981, -0.8535716153432693, -0.02090855556648028, -2.3220350435825816, -0.030267629832360667, 1.4690346631473965, 0.7142224947785337])
            self.robot.move_robot_j([0.863253819507465, -0.5490223970580519, -0.060526590153836365, -1.505593206711674, -0.023240255180332396, 0.8139228273497687, 1.0326294075855897])
            self.robot.move_robot_j([-0.49146811520560546, -0.5483666040604575, 0.008699827790391025, -1.424562310637089, -0.1584492087530014, 0.9070381476330659, 0.6617912204484846])
            self.linear_motion([0.021236, -0.265330, 0.734236, -1.571787, 0.0, 0.0])
            self.linear_motion([0.021236, -0.265330, 0.434236, -1.571787, 0.0, 0.0])
            self.linear_motion([0.021236, -0.465330, 0.434236, -1.571787, 0.0, 0.0])
            self.linear_motion([0.021236, -0.465330, 0.394236, -1.571787, 0.0, 0.0])
            self.robot.open_gripper_set_width(0.03)
            return
        except:
            self._logger.error(f'Terminating program.')
            self.camera.stop_streaming()
            exit()
    #####################    vial_pump_to_ika
    # RealSense Methods #
    #####################

    def camera_to_rack_photos_on_the_way(self):
        """
        DOES NOT FUNCTION CURRENTLY
        Takes photos of the three racks.
        """
        try:
            self.robot.close_gripper()
            self.robot.move_robot_j(self.cfg["camera_2"])
            self.robot.move_robot_j(self.cfg["camera_3"])
            self.robot.move_robot_j(self.cfg["camera_rack_3"])
            self.camera.save_picture("rack_3")
            self.robot.move_robot_j(self.cfg["camera_rack_2"])
            self.camera.save_picture("rack_2")
            self.robot.move_robot_j(self.cfg["camera_rack_1"])
            self.camera.save_picture("rack_1")
            self.robot.move_robot_j(self.cfg["camera_3"])
            self.robot.move_robot_j(self.cfg["camera_2"])
            self.robot.move_robot_j(self.cfg['start_joints_centre'])
        except:
            self._logger.error(f'Robot not available.')
            self.camera.stop_streaming()
            exit()

	###################
    # Capper methods  #
    ###################

    def remove_cap(self):
        self.robot.open_gripper_set_width(0.04)
        self.robot.move_robot_j([-1.4771949199375354, -0.572415484051916, 0.12882406991801215, -1.6454426011369938, -0.06030903326162784, 1.0330206450886197, 0.8249220554207762])
        self.robot.move_robot_j([-2.1376503852543096, -0.8151068195709036, 0.3585128535889743, -2.0192925325694837, 0.1615590325858858, 1.3105821141666834, 0.46224798753206037])
        self.robot.move_robot_j([-1.9832560473564762, -0.9353049053643878, 0.4122603149957823, -2.885654517704096, 0.3570802403792672, 1.9527389705482487, 0.6237191017642617])
        self.robot.move_robot_j([-2.031607650719508, -0.3615590271025177, 0.4142228221224064, -2.7929036992532112, 0.21931566567165334, 2.414256355868445, 0.5371665636145392])
        self.robot.move_robot_j([-2.135142131109575, -0.0969549496586894, 0.3967267971540752, -2.656576854023239, 0.004047960305793418, 2.545860109049604, 0.7746908076778054])
        self.robot.move_robot_j([-2.143532380368758, -0.03657732806774801, 0.38301829708249935, -2.671648457993092, 0.0015323795880087547, 2.6359397771780584, 0.7380644903643813])
        self.robot.open_gripper_set_width(0.01)
        self.robot.move_robot_j([-2.1259823105075424, -0.15388681818309582, 0.39072900958646795, -2.6652458580062457, 0.002301238988422685, 2.512802225059933, 0.7412386286588432])
        self.robot.move_robot_j([-2.070468321197911, -0.37761320547471966, 0.36501663189878925, -2.8522150226396374, 0.13142936526404483, 2.4477836983468793, 0.8204705723300576])
        self.robot.open_gripper_set_width(0.035)
        self.robot.move_robot_j([-1.8800464698055332, -0.7985237219040854, 0.3596394077059924, -2.779103440591309, 0.1558652045882153, 1.9819869447814094, 0.739403021086058])
        self.robot.move_robot_j([-1.7109235451630411, -0.7649867305798377, 0.21340768146514894, -1.9703134629266301, 0.07992739636037084, 1.2128431933184196, 0.7447616816279216])
        self.robot.move_robot_j([-0.8253861661291958, -0.5261716575411478, 0.0890778157665548, -1.3896348964624237, -0.045551697887494795, 0.7950331013467576, 0.8090187795565501])

    ####################
    #   Dispense Pump methods   #
    ####################

    def init_pumps(self):
        """
        Starts serial connection to the pump. Initialises the pump by force stalling. During initialisation valve connected to 
        waste port specified in the workflow configuration file.

        All ports for pump 2 are saved as 12 greater than they should be to avoid confusion
        with the dispense pump so 12 is automatically subtracted in the function calls.
        
        Returns True when connected to the XCalibur pump, False otherwise.

        """
        self._logger.info("Connecting Pump..")
        try:
            self.pump.connect()
            time.sleep(0.5)
            self.pump.is_connected()
            self._logger.info("Pump connected.")
            time.sleep(0.5)
            self.pump.initialize_device(input_port=self.dispense_dict["Waste"],output_port=self.dispense_dict["Waste"])
            self._logger.info("Pump initialised.")
            time.sleep(0.5)
            self._logger.info("Checking for pump errors")
            self.pump.check_errors() #logger in pump code will respond.
    
            #TODO adding microstepping option
          
       
        except Exception as e:
            self._logger.error("Pump not connected.")
            self._logger.error(e)
            return False

        self._logger.info("Connecting Dispense Pump 2..") 
        try:
            self.pump_2.connect()
            time.sleep(0.5)
            self.pump_2.is_connected()
            self._logger.info("Dispense Pump 2 connected.")
            time.sleep(0.5)
            self.pump_2.initialize_device(input_port=(self.dispense_dict["Waste_2"]-12),output_port=(self.dispense_dict["Waste_2"]-12))
            self._logger.info("Dispense Pump 2 initialised.")
            time.sleep(0.5)
            self._logger.info("Checking for pump errors")
            self.pump_2.check_errors() #logger in pump code will respond.
    
            #TODO adding microstepping option
            
        except Exception as e:
            self._logger.error("Dispense Pump 2 not connected.")
            self._logger.error(e)
            return False
        
        return True


    def pump_prime_reagent_tubing(self, chemical:str, prime_volume:float= 6000):
        """
        Standard reagent tubing prime - sends prime_volume (default = 6 ml)
        solvent of chosen chemical to waste port specified in workflow config file

        """

        if self.dispense_dict[chemical] <= 12:
            self._logger.info((f"{chemical} is on pump: {self.pump.device_name}"))
            self._logger.info(f'Priming reagent tubing with {chemical} from port {self.dispense_dict[chemical]} into waste on port: {self.dispense_dict["Waste"]}')
            self.pump.dispense(prime_volume, source_port = self.dispense_dict[chemical], destination_port = self.dispense_dict["Waste"])
            self.pump.is_idle()

        elif self.dispense_dict[chemical] > 12:
            self._logger.info((f"{chemical} is on pump: {self.pump_2.device_name}"))
            chemical_port = "I" + str(self.dispense_dict[chemical]-12)
            waste_port = "I" + str(self.dispense_dict["Waste_2"]-12)
            self._logger.info(f'Pump priming reagent tubing with {chemical} from port {self.dispense_dict[chemical]} into waste on port: {self.dispense_dict["Waste_2"]}')
            self.pump_2.dispense(prime_volume, source_port = chemical_port, destination_port = waste_port)
            self.pump_2.is_idle()


    def pump_expel_reagent_tubing(self, chemical:str, expel_volume:float = 6000):
        """
        Removes solvent in reagent tubing using air to push it back into storage vessels. Default volume is 6 ml. 

        """
        if self.dispense_dict[chemical] <= 12:
            self._logger.info((f"{chemical} is on pump: {self.pump.device_name}"))
            self._logger.info(f'Expelling reagent tubing with chemical: {chemical} from port {self.dispense_dict[chemical]} back into its container')
            self.pump.dispense(expel_volume, source_port = self.dispense_dict["Air"], destination_port = self.dispense_dict[chemical])
            self.pump.is_idle()

        elif self.dispense_dict[chemical] > 12:
            self._logger.info((f"{chemical} is on pump: {self.pump_2.device_name}"))
            chemical_port = "I" + str(self.dispense_dict[chemical]-12)
            air_port = "I" + str(self.dispense_dict["Air_2"]-12)

            self._logger.info(f'Expelling reagent tubing with chemical: {chemical} from port {self.dispense_dict[chemical]} back into its container')
            self.pump_2.dispense(expel_volume, source_port = air_port, destination_port = chemical_port)
            self.pump_2.is_idle()
    
    
    def pump_prime_dispense_tubing(self, chemical:str, cycle_number:int = 2):
        """
        Primes dispense line of the pump with solvent from chosen port.
        cycle_number (default 2) cycles of 1 ml washing are followed by a 1 ml prime
        
        """
        if self.dispense_dict[chemical] <= 12:
            self._logger.info((f"{chemical} is on pump: {self.pump.device_name}"))
            if chemical == self._pump_1_primed_solvent:
                self._logger.info(f"Dispense line already primed with {chemical} from port : {self.dispense_dict[chemical]}")
                
            else:
                self._logger.info(f"Priming dispense line with {chemical} from port: {self.dispense_dict[chemical]}")

                self._logger.info(f"Emptying 2 ml volume from dispense line port {self.dispense_dict['Dispense']} into waste on port '{self.dispense_dict['Waste']}")    
                self.pump.dispense(2000, source_port=self.dispense_dict["Dispense"], destination_port=self.dispense_dict["Waste"])
                cycle = 0 
                while cycle < cycle_number:
                    self._logger.info(f"Starting {cycle+1} backward washing cycle")

                    self._logger.info(f"Dispensing 1 mL {chemical} from port: {self.dispense_dict[chemical]} - overspill into waste vial")
                    self.pump.dispense(volume = 1000, source_port=self.dispense_dict[chemical], destination_port=self.dispense_dict["Dispense"])

                    self._logger.info(f"Aspirating 2 mL volume from dispense line (port: {self.dispense_dict['Dispense']}) to waste (port: {self.dispense_dict['Waste']})")
                    self.pump.dispense(volume =2000, source_port=self.dispense_dict["Dispense"], destination_port=self.dispense_dict["Waste"])
                    
                    cycle = cycle + 1

                self._logger.info(f"Priming the dispense line (port: {self.dispense_dict['Dispense']}) with {chemical} port {self.dispense_dict[chemical]}")
                self.pump.dispense(volume = 1000, source_port=self.dispense_dict[chemical], destination_port= self.dispense_dict['Dispense'])

            self._pump_1_primed_solvent = chemical #update primed solvent
            self.pump.is_idle()

        if self.dispense_dict[chemical] > 12:
            self._logger.info((f"{chemical} is on pump: {self.pump_2.device_name}"))
            dispense_port = "I" + str(self.dispense_dict["Dispense_2"]-12)
            chemical_port = "I" + str(self.dispense_dict[chemical]-12)
            waste_port = "I" + str(self.dispense_dict["Waste_2"]-12)

            if chemical == self._pump_2_primed_solvent:
                self._logger.info(f"Dispense line already primed with {chemical} from port : {self.dispense_dict[chemical]}")
            else:
                self._logger.info(f"Priming dispense line with {chemical} from port: {self.dispense_dict[chemical]}")
                self._logger.info(f"Emptying 2 ml volume from dispense line port {self.dispense_dict['Dispense_2']} into waste on port '{self.dispense_dict['Waste_2']}")    
                self.pump_2.dispense(2000, source_port=dispense_port, destination_port=waste_port)
           
            cycle = 0 
            while cycle < cycle_number:
                self._logger.info(f"Starting {cycle+1} backward washing cycle")

                self._logger.info(f"Dispensing 1 mL {chemical} from port: {self.dispense_dict[chemical]} - overspill into waste vial")
                self.pump_2.dispense(volume = 1000, source_port= chemical_port, destination_port = dispense_port)

                self._logger.info(f"Aspirating 2 mL volume from dispense line (port: {self.dispense_dict['Acid_Dispense']}) to waste (port: {self.dispense_dict['Acid_Waste']})")
                self.pump_2.dispense(volume =2000, source_port=dispense_port, destination_port=waste_port)
                
                cycle = cycle + 1

            self._logger.info(f"Priming the dispense line (port: {self.dispense_dict['Dispense_2']}) with {chemical} port {self.dispense_dict[chemical]}")
            self.pump_2.dispense(volume = 1000, source_port= chemical_port, destination_port= dispense_port)

            self._pump_2_primed_solvent = chemical #update primed solvent
            self.pump_2.is_idle()


    def dispense_volume(self, pump: Union[XCalibur,C3000SyringePump], vol:float, chemical:str, speed:int=None):
        """
        Volume dispensing of volume in uL from port specified to Dispense port specified in workflow config (1)

        For the Tecan Xcalibur pump by default the speed is predefined speed 11 (default speed) and for the C3000 pump the speed is set to 20.
        These numbers have been meassured to give accurate results for dispensing with water. 
        
        """
        if self.dispense_dict[chemical] <= 12:
            self._logger.info((f"{chemical} is on pump: {self.pump.device_name}"))
           
            if speed is not None:
                pump.set_predefined_speed(speed)

            if chemical != self._pump_1_primed_solvent:
                raise Exception(f"Need to prime with {chemical} from port {self.dispense_dict[chemical]}")
        
            self._logger.info(f"Dispensing {vol} uL of {chemical} from port {self.dispense_dict[chemical]} to dispense port ({self.dispense_dict['Dispense']})")
            pump.dispense(vol, source_port = self.dispense_dict[chemical], destination_port = self.dispense_dict['Dispense'])
            pump.is_idle()

        elif self.dispense_dict[chemical] > 12:
            self._logger.info((f"{chemical} is on pump: {self.pump_2.device_name}"))

            if speed is None:
                speed = 20
            
            if chemical != self._pump_2_primed_solvent:
                raise Exception(f"Need to prime with {chemical} from port {self.dispense_dict[chemical]}")
        
            dispense_port = "I" + str(self.dispense_dict["Dispense_2"]-12)
            chemical_port = "I" + str(self.dispense_dict[chemical]-12)

            self._logger.info(f"setting top pre-defined speed to {speed}")
            self.pump.set_predefined_speed(speed)

            self._logger.info(f"Dispensing {vol} uL of {chemical} from port {self.dispense_dict[chemical]} to dispense port ({self.dispense_dict['Dispense_2']})")
            self.pump.dispense(vol, source_port = chemical_port, destination_port = dispense_port)
            self.pump.is_idle()


    def dispense_dropwise(self, vol:float, chemical:str = "Water(DI)" ):
        """
        Volume dispensing, but dropwise, of volume in uL from port specified to Dispense port specified in workflow config (1)
        
        """
        if self.dispense_dict[chemical] <= 12:
            self._logger.info(f"Dropwise dispensing {vol} uL of {chemical}")
            self.pump.set_predefined_speed(speed = 14)
            self.dispense_volume(vol, chemical)
            self.pump.set_predefined_speed(11) # resetting to default after dropwise dispensing is done
        
        elif self.dispense_dict[chemical] > 12:
            self._logger.info(f"Dropwise dispensing {vol} uL of {chemical}")
            self.pump_2.set_predefined_speed(speed=27)
            self.dispense_volume(vol, chemical)
            self.pump_2.set_predefined_speed(20)
        



    #######################
    # Pump holder methods #
    #######################
    def hold_position(self):
        '''
        
        '''
        self._logger.info("Moving holder to home position...")
        self.holder.holding_position()
        time.sleep(6)
    
    def infuse_position(self):
        '''
        
        '''
        self._logger.info("Moving holder to infusing position...")
        self.holder.infusing_position()
        time.sleep(6)

    #######################
    # Filter Machine Init #
    #######################

    def init_filt_machine(self):
        '''
        
        '''
        try:
            self._logger.info("Initialising the filter machine")
            self.filt_machine.initialise_filtmachine()

            return True
        
        except Exception as e:
            self._logger.error("Filter machine not connected.")
            self._logger.error(e)
            return False

    ###################
    # Quantos methods #
    ###################
    def tare(self):
        """
        Tares the Quantos
        
        """
        time.sleep(5)
        self._logger.info("Taring Quantos")
        self.quantos.tare()
        time.sleep(5)

    def zero(self):
        """
        Zeros the Quantos
        
        """
        time.sleep(5)
        self._logger.info("Zeroing Quantos")
        self.quantos.zero()
        time.sleep(5)

    def set_antistatic(self, pause=5):
        """
        Toggles antistatic for a certain time
        pause: value in seconds for which antistatic is on
        
        """
        self._logger.info(f"Setting antistatic on for {pause} secs")
        self.quantos.set_antistatic_on()
        time.sleep(pause)
        self._logger.info("Setting antistatic off")
        self.quantos.set_antistatic_off()

    def take_weight(self) -> float:
        """
        Measures stable weight currently on Quantos
        Includes 20 seconds of antistatic 
        
        returns: mass in g as a float.
        """
        time.sleep(5)
        self.set_antistatic(pause = 20)
        self._logger.info("Getting stable weight")
        weight = self.quantos.get_stable_weight()
        self._logger.info(f"Stable weight is: {weight}")
        return weight['outcomes'][1]
    
    def record_weight(self, sample_name, file_name, weight):
        """
        Records a weight to a results file with an associated time the mass was logged,
        
        sample_name = name of sample being weighed
        file_name = name of results file (will append result if does not exist, will create it if it does)
        weightL mass in grams
        
        """
        path = "data/results/"+file_name
        if os.path.exists(path):
            self._logger.debug("Results file exists - writing to it")
            f = open(path, "a+") 
            f.write(f'{sample_name} \t {weight}\t {datetime.datetime.now()} \n')

        else: 
            self._logger.debug("No results file for weight exists - creating one")
            f = open(path, "a+")
            f.write("Sample Name\t Mass (g):\t Time: \n")
            f.write(f'{sample_name} \t {weight}\t {datetime.datetime.now()} \n')
    
    def shut_door(self):
        """
        Shuts front and side doors of the Quantos
        """
        self._logger.info("Shutting Quantos doors")
        self.quantos.close_front_door()
        self.quantos.close_side_door()
    
    def init_quantos(self):
        """
        Initialises the Quantos opening the front and side doors and unlocking the dosing head pin
        Returns True when connected to quantos, False otherwise.
        """
        try:
            self._logger.info("Connecting to the Quantos - opening doors")
            side = self.quantos.open_side_door()
            time.sleep(1)
            front = self.quantos.open_front_door()
            time.sleep(4)
            pin = self.quantos.unlock_dosing_head_pin()
            self._logger.info("Quantos connected..")
            if side["success"] and front["success"] and pin["success"] == True:
                return True
        except:
            self._logger.error("Quantos not connected..")
            return False
    
    def quantos_dosing(self,quantity=0, tolerance = 5) -> float:
        """
        Runs antistatic for 30 seconds
        Closes front and side doors and doses a given quantity. When finishes dosing, it opens the doors.
        Weighs the sample 3 times and returns the final mass as a float

        """
        self._logger.info("setting antistatinc on for 30 seconds")
        self.quantos.set_antistatic_on()
        time.sleep(30) 
        self.quantos.set_antistatic_off()
        self._logger.info("Closing the Quantos doors")
        self.quantos.close_front_door()
        self.quantos.close_side_door()
        time.sleep(2)
        self._logger.info("Taring the vial")
        self.quantos.tare()
        self._logger.info(f"Setting target mass: {quantity} mg")
        x = self.quantos.set_target_mass(quantity)
        self._logger.info(f"Setting tolerance to: {tolerance} %")
        x = self.quantos.set_tolerance_value(tolerance)
        self._logger.info("Starting dosing")
        self.quantos.start_dosing()
        self._logger.info("Weighing after dosing...") # Weigh three times
        mass_1 = self.take_weight()
        mass_2 = self.take_weight()
        mass_3 = self.take_weight()
        self._logger.info(f"Mass measurement 3: {mass_3}")
        self._logger.info("Opening Quantos doors")
        self.quantos.open_side_door()
        self.quantos.open_front_door()
        self._logger.info("Unlocking dosing head pin")
        unlock = self.quantos.unlock_dosing_head_pin()
        if not (unlock['success']==True):
            self._logger.error("Dosing pin did not unlock!")
            self.camera.stop_streaming()
            exit()
        time.sleep(2)
        return mass_3
    
    def check_quantos_door_position(self, debug = False):
        """
        Checks if the Quantos front door is open  
        """

        self._logger.info("Quantos door check")
        
        front = self.quantos.get_front_door_position()
        side = self.quantos.get_side_door_position()

        if not (front['outcomes'][0]=='Open position' and side['outcomes'][0] == True):
            self._logger.error("[ERROR] The quantos front door is closed, this may lead to collitions.")
            self._logger.error("[ERROR] Terminating program.")
            self.camera.stop_streaming()
            exit()
        else:
            self._logger.info("Door is open - check is passed")
        if debug:
            self._logger.warning("Debug mode is active - no door position being checked")

    def check_quantos_cartridge(self):
        """
        Terminates the program if the robot fails to mount the cartridge in order to avoid the quantos station to close the front when the robot is on the way.
        """
        if self.quantos.get_head_data()['outcomes'][0]=='Not mounted':
            self._logger.error("Cartridge not mounted terminating program.")
            exit()
        else:
            self._logger.info("Cartridge mounted ",self.quantos.get_head_data()['outcomes'][0])
  

    ###################
    # System Logger #
    ###################

    def start_system_logger(self, filename, logging_level = "INFO"):
        """
        Starts the instrument logger for the system. 
        filename = name of the log file
        logging_level = level that logging is done at - INFO, DEBUG or ERROR

        """
       
        fh = logging.FileHandler(f'{LOG_PATH}/{filename}.log')
        sh = logging.StreamHandler(stream = sys.stdout)
        
        if logging_level == "INFO":
            fh.setLevel(logging.INFO)
            sh.setLevel(logging.INFO)

        elif logging_level == "DEBUG":
            fh.setLevel(logging.DEBUG)
            sh.setLevel(logging.DEBUG)

        elif logging_level == "ERROR":
            fh.setLevel(logging.ERROR)
            sh.setLevel(logging.ERROR)

        else:
            print("[ERROR] Incorrect logger level set")
            exit()
        
        logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[fh, sh],
        level = logging.DEBUG)
        
        self._logger = logging.getLogger("RiH_Main")

    #############################
    # Filtering station methods #
    #############################
    
    def pick_up_filtering_catridge(self):
        self.robot.open_gripper()
        self.robot.move_robot_j([-0.015693228366082175, -0.49812670192091124, -0.0065036366337090324, -1.3073964135079714, 0.03463181658254454, 0.786609793610043, 0.8149505945726105])
        self.robot.move_robot_j([1.674659418624744, -0.41532781392231316, -0.19132873252028346, -1.3001698934209276, 0.0343233674135473, 0.7842199078848138, 0.7947089139614858])
        self.robot.move_robot_j([1.674149695513541, -0.6897074097147342, -0.17725382302024767, -2.1739502764250105, -0.08814549636178547, 1.4943245419926112, 0.7041915424838662])
        self.robot.move_robot_j([1.7456235150956267, -0.5439646827379863, -0.15957125045123846, -2.0740535511552243, -0.09231727998786594, 1.4998161822414235, -0.7254403209512431])
        self.linear_motion([0.021982, 0.371151, 0.526305, 3.1116, 0.0, 0.0])
        self.linear_motion([0.001982, 0.376151, 0.526305, 3.1116, 0.0, 0.0])
        self.linear_motion([-0.011982, 0.376151, 0.526305, 3.1116, 0.0, 0.0])
        self.linear_motion([-0.041982, 0.376051, 0.526305, 3.1116, 0.0, 0.0])
        self.robot.gripper.clamp()    
        self.linear_motion([-0.041982, 0.376151, 0.540705, 3.1116, 0.0, 0.0])
        self.linear_motion([0.169982, 0.375151, 0.540705, 3.1116, 0.0, 0.0])
        self.robot.move_robot_j([1.3810990672865433, -0.4376424354630252, -0.16643925884942884, -1.9463214740920483, -0.07087051429637338, 1.5159071390893721, 0.41702839089840543])
        self.linear_motion([0.165462, 0.375898, 0.547361, 1.594442, 0.0, 0.0])
        self.linear_motion([0.155462, 0.385898, 0.547361, 1.594442, 0.0, 0.0])
        self.linear_motion([0.145462, 0.450898, 0.547361, 1.594442, 0.0, 0.0])
        self.linear_motion([0.145462, 0.450898, 0.427361, 1.594442, 0.0, 0.0])
        self.linear_motion([0.155462, 0.455898, 0.427361, 1.594442, 0.0, 0.0])
        self.linear_motion([0.155462, 0.455898, 0.427361, 1.594442, 0.0, 0.0])
        self.linear_motion([0.155462, 0.455898, 0.407361, 1.594442, 0.0, 0.0])
        self.linear_motion([0.155462, 0.455898, 0.403361, 1.594442, 0.0, 0.0])
        self.robot.open_gripper()
        self.linear_motion([0.155462, 0.445898, 0.403361, 1.594442, 0.0, 0.0])
        self.robot.move_robot_j([1.4180408426581297, -0.40603677229142937, -0.20012302592944792, -2.2876534836625964, -0.07338749797476662, 1.8745120645772564, 0.4227108383352557])
        self.robot.move_robot_j([1.4025843011956465, -0.7236015141422236, -0.20296927823843228, -2.3376190340811744, -0.07817199697564226, 1.5571044008783577, 0.4598264976516365])
        self.robot.move_robot_j([1.4551312539545598, -0.4365661676557441, -0.21932228113610006, -1.3286644837396187, 0.024738479376876267, 0.8042131334707229, 0.39049909235785407])
        self.robot.move_robot_j([-0.050447479366976446, -0.47775928589335653, 0.01790303542896321, -1.2537099689851727, 0.02443178229839522, 0.719573510593838, 0.8102711208835244]) 
        #self.robot.move_robot_j([1.6719688030542637, -0.8834351108366983, -0.26671000717412824, -2.2992954718941134, -0.21853025324254666, 1.4411707397379108, 1.4808894478894459]) 
        #self.robot.move_robot_j() 

    def place_pouring_vial(self):
        self.robot.open_gripper()
        #self.robot.move_robot_j([-0.05020420201233077, -0.4773133730470087, 0.01744419895303219, -1.2543397719901905, 0.02371481578714317, 0.7202882735994127, 0.8095652515489441])
        #self.robot.move_robot_j([-1.6873949912723742, -0.6481646969415631, 0.17068669062539152, -1.5021913855719906, -0.017016506136498518, 0.8197445568508572, 0.9085084088042592])
        #self.robot.move_robot_j([-1.6641150814357553, -0.9656199755166707, 0.1150808939664439, -2.631869816296348, 0.07034483932520205, 1.6645764294422867, 0.7613252695575357])
        #self.robot.move_robot_j([-1.6667833183522565, -0.41091312391725665, 0.13329024939710454, -2.307009343369095, 0.06706399340099758, 1.895795737698075, 0.8152373406402784])
        #self.linear_motion([0.022258, -0.427369, 0.398940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.022258, -0.467369, 0.398940, -1.595905, 0.0, 0.0])
        self.robot.gripper.clamp()
        self.linear_motion([0.022258, -0.467369, 0.418940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.022258, -0.367369, 0.418940, -1.595905, 0.0, 0.0])
        self.robot.move_robot_j([-1.6825831973092593, -0.7512689684489675, 0.10107567072019243, -1.4848797843832717, 0.050245032940314245, 0.7522517192800073, 0.9702840447599688])
        self.robot.move_robot_j([0.025837634441163083, -0.5176102407355057, 0.03080867797267018, -1.3993947949827763, -0.02509436809981876, 0.7529030797853492, 0.8734131455595293])
        self.robot.move_robot_j([1.750326817479648, -0.44464414172915323, -0.23112342370038044, -1.390864142585219, -0.014127235525181456, 0.9074308650758531, 0.8713202182625731])
        self.robot.move_robot_j([1.6719688030542637, -0.8834351108366983, -0.26671000717412824, -2.2992954718941134, -0.21853025324254666, 1.4411707397379108, 1.4808894478894459])
        self.robot.move_robot_j([1.7415798643011793, -0.0069504058194177895, -0.46784280477804047, -1.5596739162143904, -0.02469401671323521, 1.555493745115068, 1.2319450958743936])
        self.robot.move_robot_j([1.7415834835788657, -0.006952786336996053, -0.4678375150644988, -1.5596669560649934, -0.02469401671323511, 1.5554923209614222, 1.2319494700597393])
        self.robot.move_robot_j([1.7521364097260588, -0.05325885548002933, -0.4686465469368717, -1.670775921484095, -0.04249728541703545, 1.6499860881446284, 1.2195799009179076])
        self.linear_motion([0.167485, 0.522769, 0.506766, 0.852446, 0.0, 0.0])
        self.linear_motion([0.167485, 0.522769, 0.479766, 0.852446, 0.0, 0.0])
        self.robot.open_gripper_set_width(0.03)
        self.linear_motion([0.167485, 0.522769, 0.506766, 0.852446, 0.0, 0.0])
        self.robot.move_robot_j([1.8239471924765067, -0.2191294359424024, -0.41650516700744616, -1.457997336354172, -0.015636471908125612, 1.188983913368649, 1.2006505843130706])
        self.robot.move_robot_j([1.4417549399440945, -0.30650558163038505, -0.06792560008212559, -1.1878539450628716, -0.015183169519735707, 0.7825317940182156, 0.7487085182201909])
        self.robot.move_robot_j([0.04891864797682642, -0.36952059863329684, -0.034476075749482936, -1.087221138013657, -0.015606996442708701, 0.6221409357674151, 0.7824923388328234])
        #self.robot.move_robot_j()
    def place_pouring_cleaning_vial(self,vial_number):
        self.vial_rack_to_pump(vial_number=vial_number)
        self.linear_motion([0.022258, -0.467369, 0.398940, -1.595905, 0.0, 0.0])
        self.robot.gripper.clamp() 
        self.linear_motion([0.022258, -0.467369, 0.418940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.022258, -0.367369, 0.418940, -1.595905, 0.0, 0.0])
        self.robot.move_robot_j([-1.6825831973092593, -0.7512689684489675, 0.10107567072019243, -1.4848797843832717, 0.050245032940314245, 0.7522517192800073, 0.9702840447599688])
        self.robot.move_robot_j([0.025837634441163083, -0.5176102407355057, 0.03080867797267018, -1.3993947949827763, -0.02509436809981876, 0.7529030797853492, 0.8734131455595293])
        self.robot.move_robot_j([1.750326817479648, -0.44464414172915323, -0.23112342370038044, -1.390864142585219, -0.014127235525181456, 0.9074308650758531, 0.8713202182625731])
        self.robot.move_robot_j([1.6719688030542637, -0.8834351108366983, -0.26671000717412824, -2.2992954718941134, -0.21853025324254666, 1.4411707397379108, 1.4808894478894459])
        self.robot.move_robot_j([1.7415798643011793, -0.0069504058194177895, -0.46784280477804047, -1.5596739162143904, -0.02469401671323521, 1.555493745115068, 1.2319450958743936])
        self.robot.move_robot_j([1.7415834835788657, -0.006952786336996053, -0.4678375150644988, -1.5596669560649934, -0.02469401671323511, 1.5554923209614222, 1.2319494700597393])
        self.robot.move_robot_j([1.7521364097260588, -0.05325885548002933, -0.4686465469368717, -1.670775921484095, -0.04249728541703545, 1.6499860881446284, 1.2195799009179076])
        self.linear_motion([0.167485, 0.522769, 0.506766, 0.852446, 0.0, 0.0])
        self.linear_motion([0.167485, 0.522769, 0.479766, 0.852446, 0.0, 0.0])
        self.robot.open_gripper_set_width(0.03)
        self.linear_motion([0.167485, 0.522769, 0.506766, 0.852446, 0.0, 0.0])
        self.robot.move_robot_j([1.8239471924765067, -0.2191294359424024, -0.41650516700744616, -1.457997336354172, -0.015636471908125612, 1.188983913368649, 1.2006505843130706])
        self.robot.move_robot_j([1.4417549399440945, -0.30650558163038505, -0.06792560008212559, -1.1878539450628716, -0.015183169519735707, 0.7825317940182156, 0.7487085182201909])
        self.robot.move_robot_j([0.04891864797682642, -0.36952059863329684, -0.034476075749482936, -1.087221138013657, -0.015606996442708701, 0.6221409357674151, 0.7824923388328234])
    def remove_pouring_vial(self,vial_number):
        self.robot.open_gripper_set_width(0.03)
        self.robot.move_robot_j([0.04891864797682642, -0.36952059863329684, -0.034476075749482936, -1.087221138013657, -0.015606996442708701, 0.6221409357674151, 0.7824923388328234])
        self.robot.move_robot_j([1.4417549399440945, -0.30650558163038505, -0.06792560008212559, -1.1878539450628716, -0.015183169519735707, 0.7825317940182156, 0.7487085182201909])
        self.robot.move_robot_j([1.8239471924765067, -0.2191294359424024, -0.41650516700744616, -1.457997336354172, -0.015636471908125612, 1.188983913368649, 1.2006505843130706])
        self.linear_motion([0.167485, 0.522769, 0.506766, 0.852446, 0.0, 0.0])
        self.linear_motion([0.167485, 0.522769, 0.479766, 0.852446, 0.0, 0.0])
        self.robot.gripper.clamp()
        self.linear_motion([0.167485, 0.522769, 0.506766, 0.852446, 0.0, 0.0])
        self.robot.move_robot_j([1.7521364097260588, -0.05325885548002933, -0.4686465469368717, -1.670775921484095, -0.04249728541703545, 1.6499860881446284, 1.2195799009179076])
        self.robot.move_robot_j([1.7415834835788657, -0.006952786336996053, -0.4678375150644988, -1.5596669560649934, -0.02469401671323511, 1.5554923209614222, 1.2319494700597393])
        self.robot.move_robot_j([1.7415798643011793, -0.0069504058194177895, -0.46784280477804047, -1.5596739162143904, -0.02469401671323521, 1.555493745115068, 1.2319450958743936])
        self.robot.move_robot_j([1.750326817479648, -0.44464414172915323, -0.23112342370038044, -1.390864142585219, -0.014127235525181456, 0.9074308650758531, 0.8713202182625731])
        self.robot.move_robot_j([0.025837634441163083, -0.5176102407355057, 0.03080867797267018, -1.3993947949827763, -0.02509436809981876, 0.7529030797853492, 0.8734131455595293])
        self.robot.move_robot_j([-1.6825831973092593, -0.7512689684489675, 0.10107567072019243, -1.4848797843832717, 0.050245032940314245, 0.7522517192800073, 0.9702840447599688])
        self.linear_motion([0.022258, -0.367369, 0.418940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.022258, -0.467369, 0.418940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.022258, -0.467369, 0.398940, -1.595905, 0.0, 0.0])
        self.robot.open_gripper_set_width(0.03) 
        self.vial_pump_to_rack(vial_number=vial_number)
        #############################

    def place_filtered_vial(self,vial_number):
        self.vial_rack_to_pump(vial_number=vial_number)
        self.linear_motion([0.022258, -0.467369, 0.398940, -1.595905, 0.0, 0.0])
        self.robot.gripper.clamp()
        self.linear_motion([0.022258, -0.467369, 0.418940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.022258, -0.367369, 0.418940, -1.595905, 0.0, 0.0])
        self.robot.move_robot_j([-1.6825831973092593, -0.7512689684489675, 0.10107567072019243, -1.4848797843832717, 0.050245032940314245, 0.7522517192800073, 0.9702840447599688])
        self.robot.move_robot_j([0.025837634441163083, -0.5176102407355057, 0.03080867797267018, -1.3993947949827763, -0.02509436809981876, 0.7529030797853492, 0.8734131455595293])
        self.robot.move_robot_j([1.750326817479648, -0.44464414172915323, -0.23112342370038044, -1.390864142585219, -0.014127235525181456, 0.9074308650758531, 0.8713202182625731])
        self.robot.move_robot_j([1.6719688030542637, -0.8834351108366983, -0.26671000717412824, -2.2992954718941134, -0.21853025324254666, 1.4411707397379108, 1.4808894478894459])
        self.robot.move_robot_j([1.6281430118964195, -0.3980067594586163, -0.6486899381185833, -2.5686961688995167, -0.33876235405132293, 2.2284462699539764, 0.44566595754772426])
        self.robot.move_robot_j([1.779449390942155, -0.2524978374472835, -0.6574094391538323, -2.3812009145131943, -0.24718411427074002, 2.1793000150786535, 0.48752772413047285])
        self.robot.move_robot_j([1.783870984194372, -0.11279546735370369, -0.7080851416671484, -2.329660907236197, -0.1511637922260496, 2.2151418075031706, 0.3602497911627094])
        self.linear_motion([0.242288, 0.425569, 0.267143, 1.596921, 0.0, 0.0])
        self.linear_motion([0.242288, 0.425569, 0.247143, 1.596921, 0.0, 0.0])
        self.robot.open_gripper_set_width(0.03)
        self.linear_motion([0.242288, 0.375569, 0.247143, 1.596921, 0.0, 0.0])
        self.robot.move_robot_j([1.5006457277599135, -0.6531259591905769, -0.20413154550438192, -2.2995178853085165, -0.1337984819014867, 1.6078263387150236, 0.5208376335718204])
        self.robot.move_robot_j([1.5719450108374318, -0.4848362044535184, -0.16404195932547253, -1.3822260693165294, 0.06553822645213869, 0.9770391910341051, 0.6686057488357239])
        self.robot.move_robot_j([-0.016817075523387067, -0.47763799082550246, 0.022284079694352317, -1.307106972314338, -0.003169188798304499, 0.7513545625414153, 0.7695980900152205])
    def remove_filtered_vial(self,vial_number):
        self.robot.open_gripper_set_width(0.03)
        self.robot.move_robot_j([-0.016817075523387067, -0.47763799082550246, 0.022284079694352317, -1.307106972314338, -0.003169188798304499, 0.7513545625414153, 0.7695980900152205])
        self.robot.move_robot_j([1.5719450108374318, -0.4848362044535184, -0.16404195932547253, -1.3822260693165294, 0.06553822645213869, 0.9770391910341051, 0.6686057488357239])
        self.robot.move_robot_j([1.5006457277599135, -0.6531259591905769, -0.20413154550438192, -2.2995178853085165, -0.1337984819014867, 1.6078263387150236, 0.5208376335718204])
        self.linear_motion([0.242288, 0.375569, 0.243143, 1.596921, 0.0, 0.0])
        self.linear_motion([0.242288, 0.425569, 0.243143, 1.596921, 0.0, 0.0])
        self.robot.gripper.clamp()
        self.linear_motion([0.242288, 0.425569, 0.267143, 1.596921, 0.0, 0.0])
        self.robot.move_robot_j([1.6719688030542637, -0.8834351108366983, -0.26671000717412824, -2.2992954718941134, -0.21853025324254666, 1.4411707397379108, 1.4808894478894459])
        self.robot.move_robot_j([1.750326817479648, -0.44464414172915323, -0.23112342370038044, -1.390864142585219, -0.014127235525181456, 0.9074308650758531, 0.8713202182625731])
        self.robot.move_robot_j([0.025837634441163083, -0.5176102407355057, 0.03080867797267018, -1.3993947949827763, -0.02509436809981876, 0.7529030797853492, 0.8734131455595293])
        self.robot.move_robot_j([-1.6825831973092593, -0.7512689684489675, 0.10107567072019243, -1.4848797843832717, 0.050245032940314245, 0.7522517192800073, 0.9702840447599688])
        self.linear_motion([0.022258, -0.367369, 0.418940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.022258, -0.467369, 0.418940, -1.595905, 0.0, 0.0]) 
        self.linear_motion([0.022258, -0.467369, 0.398940, -1.595905, 0.0, 0.0])
        self.robot.open_gripper_set_width(0.03)
        ##TODO capping here
        self.vial_pump_to_capper(to_home=True)
        self.cap()
        self.vial_capper_to_pump()
        ####
        self.vial_pump_to_rack(vial_number=vial_number)

    def vial_decap(self,vial_number):
        self.vial_rack_to_pump(vial_number=vial_number)
        self.linear_motion([0.022258, -0.467369, 0.398940, -1.595905, 0.0, 0.0])
        self.robot.gripper.clamp()
        self.linear_motion([0.022258, -0.467369, 0.418940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.022258, -0.367369, 0.418940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.172258, -0.367369, 0.418940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.172258, -0.367369, 0.148940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.192258, -0.417369, 0.148940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.192258, -0.417369, 0.124940, -1.595905, 0.0, 0.0])
        self.robot.open_gripper_set_width(0.05) ##**
        self.linear_motion([0.192258, -0.417369, 0.154940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.192258, -0.367369, 0.154940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.192258, -0.367369, 0.204940, -1.595905, 0.0, 0.0])
        ##DECAP HERE
        self.capper.right()
        self.linear_motion([-0.092258, -0.367369, 0.204940, -1.595905, 0.0, 0.0])
        self.linear_motion([-0.092258, -0.397369, 0.204940, -1.595905, 0.0, 0.0])
        time.sleep(80)
        self.linear_motion([-0.092258, -0.397369, 0.144940, -1.595905, 0.0, 0.0])
        self.linear_motion([-0.092258, -0.407369, 0.144940, -1.595905, 0.0, 0.0])
        self.robot.gripper.clamp()
        #self.robot.open_gripper_set_width(0.025)
        self.linear_motion([-0.092258, -0.407369, 0.174940, -1.595905, 0.0, 0.0])
        self.linear_motion([-0.092258, -0.337369, 0.174940, -1.595905, 0.0, 0.0])
        self.capper.left()
        self.robot.open_gripper_set_width(0.03) 
        self.linear_motion([-0.002258, -0.337369, 0.174940, -1.595905, 0.0, 0.0])
        self.linear_motion([-0.092258, -0.397369, 0.204940, -1.595905, 0.0, 0.0])
        self.linear_motion([-0.092258, -0.367369, 0.204940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.192258, -0.367369, 0.204940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.192258, -0.367369, 0.154940, -1.595905, 0.0, 0.0])
        time.sleep(68)
        self.linear_motion([0.192258, -0.417369, 0.154940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.192258, -0.417369, 0.124940, -1.595905, 0.0, 0.0])
        self.robot.gripper.clamp()
        self.linear_motion([0.192258, -0.417369, 0.148940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.172258, -0.367369, 0.148940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.172258, -0.367369, 0.418940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.022258, -0.367369, 0.418940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.022258, -0.467369, 0.418940, -1.595905, 0.0, 0.0])
        self.linear_motion([0.022258, -0.467369, 0.398940, -1.595905, 0.0, 0.0])
        self.robot.open_gripper_set_width(0.03)
        
        
    
