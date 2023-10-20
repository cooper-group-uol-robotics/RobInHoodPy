from frankx import Affine, LinearRelativeMotion, Robot, Gripper
from src.frankx_helpers import FrankxHelpers
from conf.configuration import *
import time
from pylabware import RCTDigitalHotplate,XCalibur,QuantosQB1
from drivers.camera import Camera
from drivers.timer import Timer

class RobInHood():
    """
    This class connects with Panda robot.
    """
    def __init__(self, conf_path=FILENAME, ip=PANDA_IP, sim=True, vel=0.05 ):
        """
        This constructor takes as input the filename, ip and sim.
        
        :param filename: is a string containing the file's path where the joints positions of the Panda robot were saved.
        :type: string
        :param ip: is a string containing the IP address of the Panda's robot API.
        :type: string
        :param sim: is a bool value that allows to run the code in sumulation mode when set to True 
        :type: bool
        :param vel: it is used to set the velocity of the robot which goes from 0.01 to 1.0
        :type: float
        """
        self.cfg=read_json_cfg(conf_path)
        self.robot=None
        self.state=None
        self.ip=ip
        self.sim=sim
        self.vel=vel
        self.ika=RCTDigitalHotplate(device_name="IKA", connection_mode='serial', address='', port= IKA_PORT)
        self.pump = XCalibur('PUMP', 'serial', port = PUMP_PORT, switch_address="0",address="1")
        self.quantos=QuantosQB1(device_name="QUANTOS", connection_mode="serial", port=QUANTOS_PORT)
        self.camera=Camera()
        self.timer=Timer()
        self.camera_connected=self.init_camera()
        self.ika_connected=self.init_ika()
        self.pump_connected=self.init_pump()
        self.quantos_connected=self.init_quantos()
        self.robot_connected=self.init_robot()
        self.devices_connected_report()
    
    def devices_connected_report(self):
        """
        Terminates the program if one of the devices is not available.
        """
        if not self.camera_connected:
            print("[ERROR] Camera is not available.")
        if not self.ika_connected:
            print("[ERROR] IKA station is not available.")
        if not self.pump_connected:
            print("[ERROR] xCalibur Pump is not available.")
        if not self.quantos_connected:
            print("[ERROR] Quantos is not connected.")
        if not self.robot_connected:
            print("[ERROR] Robot not available or the emergency stop button is activated.")
        if not self.robot_connected or not self.quantos_connected or not self.pump_connected or not self.ika_connected or not self.camera_connected:
            print("[ERROR] Terminating the program.")
            if self.camera_connected:
                self.camera.stop_streaming()
            exit()
    
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
    ###### Quantos control methods ###################
    def init_quantos(self):
        """
        Returns True when connected to quantos, False otherwise.
        """
        try:
            print("[INFO] Connecting Quantos..")
            self.quantos.open_side_door()
            time.sleep(1)
            self.quantos.open_front_door()
            time.sleep(5)
            self.quantos.unlock_dosing_head_pin()
            print("[INFO] Quantos connected..")
            return True
        except:
            print("[ERROR] Quantos not connected..")
            return False
    def quantos_dosing(self,quantity=0):
        """
        Closes front and side doors and doses a given quantity. When finishes dosing, it opens the doors.
        """
        self.quantos.close_front_door()
        self.quantos.close_side_door()
        time.sleep(2)
        self.quantos.set_target_mass(quantity)
        self.quantos.start_dosing()
        self.quantos.open_side_door()
        self.quantos.open_front_door()
        self.quantos.unlock_dosing_head_pin()
        time.sleep(2)
        return self.quantos.get_sample_data()
    def check_quantos_door_position(self):
        """
        Terminates the program when the door is closed, aiming to avoid the robot to collide against the mettler. 
        """
        if not (self.quantos.get_front_door_position()['outcomes'][0]=='Open position'):
            print("[ERROR] The quantos front door is closed, this may lead to collitions.")
            print("[ERROR] Terminating program.")
            self.camera.stop_streaming()
            exit()
    def check_quantos_cartridge(self):
        """
        Terminates the program if the robot fails to mount the cartridge in order to avoid the quantos station to close the front when the robot is on the way.
        """
        if self.quantos.get_head_data()['outcomes'][0]=='Not mounted':
            print("[ERROR] Cartridge not mounted terminating program.")
            exit()
        else:
            print("[INFO] Cartridge mounted ",self.quantos.get_head_data()['outcomes'][0])
    ########## Pump control methods ######################
    def init_pump(self):
        """
        Returns True when connected to the xCalibur pum, False otherwise.
        """
        print("[INFO] Connecting Pump..")
        try:
            self.pump.connect()
            time.sleep(0.5)
            self.pump.is_connected()
            print("[INFO] Pump connected.")
            time.sleep(0.5)
            self.pump.initialize_device()
            print("[INFO] Pump inisialised.")
            time.sleep(0.5)
            pump_errors = self.pump.check_errors()
            #print("[INFO] ", pump_errors)
            #TODO adding microstepping option
            return True
        except Exception as e:
            print("[ERROR] Pump not connected.")
            print(e)
            return False
    def pump_inyect(self,input_source="I3",output="I3",quantity=5000,repeat=1):
        """
        Inyects a given quantity and repeats the cicle the times given by repeat
        :param input_source: I3, I4, ..., I12
        :param output: I1 to vial and I2 goes to the left overs vial.
        :param quantity: 3000 = 1 ml 40000 =1 ml for microstepping ...
        :param repeat: This is the number of times the shringe repeats a cicle (fills, inyects). 
        """
        try:
            for i in range(0,repeat):
                self.pump.move_plunger_absolute(0)
                print('[INFO] Plunger moved to absolute 0.')
                time.sleep(1.5)
                self.pump.set_valve_position(input_source)
                print(f'[INFO] Pump valve input set to {input_source}.')
                self.pump.move_plunger_absolute(quantity)
                print(f'[INFO] Pump inyecting {quantity}.')
                time.sleep(1.5)
                self.pump.set_valve_position(output)
                print(f'[INFO] Pump valve set to {output}.')
                self.pump.move_plunger_absolute(0)
                print(f'[INFO] Plunger moved to absolute 0.')
                time.sleep(2)
        except:
            print("[ERROR] Pump not connected.")
    ###### IKA control methods ###################################
    def init_ika(self,default_speed=500):
        """
        Returns True when IKA has been connected, False otherwise.
        """
        print("[INFO] Connecting IKA RCT digital..")
        try:
            self.ika.connect()
            time.sleep(2)
            self.ika.is_connected()
            print("[INFO] IKA RCT digital connected.")
            time.sleep(1.5)
            self.ika.set_speed(default_speed)
            print(f'[INFO] Stiring velocity set to {default_speed}.')
            time.sleep(1.5)
            temperature=self.ika.get_temperature()
            print(f'[INFO] Current temperature: {temperature}.')
            return True
        except:
            print("[ERROR] IKA RCT not connected.")
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
                print(f'[INFO] Panda robot connected to {self.ip}')
                print('[INFO] Current Pose: ', self.robot.robot.current_pose())
                #print('[INFO] O_TT_E: ', self.state.O_T_EE)
                #print('[INFO] Joints: ', self.state.q)
                #print('[INFO] Elbow: ', self.state.elbow)
                return True
            except:
                print("[ERROR] Robot not connected...") 
                return False  	
        else:
            print("[WARNING] Robot running in simulation mode.")
            return True
	
    def go_home(self):
        """
        This method moves the robot to its home position in the Hood. 

        WARNING: Since the robot is located in a constrained space, calling this method from a position where the robot is away from the home position may lead to potential crashes. 
        :return: None
        """
        if not self.sim:
            print("[INFO] Robot moving to home..")
            self.robot.move_robot_j(self.cfg['start_joints_centre'])
            return 
        else:
            print("[INFO] Robot moving to home..")
            return
	###################### Cartridge Manipulation methods ############################	
    def pick_up_cartridge_from_holder(self, cartridge_number = 1):
        """
        Picks the cartridge from its holder.
        Terminates the program if the quantos front door is closed in order to avoid any collisions.  
        """
        self.check_quantos_door_position()
        try:
            print("[INFO] Robot picking up cartridge ... ")
            self.robot.open_gripper()
            self.robot.move_robot_j(self.cfg['start_joints_robot_right'])
            self.robot.move_robot_j(self.cfg[f'above_cartridge_{cartridge_number}_in_holder'])
            self.robot.move_robot_j(self.cfg[f'grasping_cartridge_{cartridge_number}_in_holder'])
            self.robot.close_gripper()
            self.robot.move_robot_j(self.cfg[f'above_cartridge_{cartridge_number}_in_holder'])
            self.robot.move_robot_j(self.cfg['start_joints_robot_right'])
            self.robot.move_robot_j(self.cfg['start_joints_centre'])
            return 
        except:
            print("[ERROR] Cartridge not available.")
            self.camera.stop_streaming()
            exit()

    def insert_cartridge_in_quantos(self, cartridge_number = 1):
        """
        Inserts the cartridge into quantos. 
        Terminates the program if the quantos front door is closed in order to avoid any collisions.  
        """
        self.check_quantos_door_position()
        try:
            print("[INFO] Robot inserting cartridge ... ")
            self.robot.move_robot_j(self.cfg['start_joints_robot_left'])
            self.robot.move_robot_j(self.cfg['midway_robot_left'])
            self.robot.move_robot_j(self.cfg[f'cartridge_adjust_for_insertion_{cartridge_number}'])
            self.robot.move_robot_j(self.cfg[f'cartridge_midwaypoint_to_prepare_for_insertion_{cartridge_number}'])  
            self.robot.move_robot_j(self.cfg[f'cartridge_prepare_for_insertion_{cartridge_number}'])  
            self.robot.move_robot_j(self.cfg[f'cartridge_insertion_new_{cartridge_number}']) 
            self.robot.move_robot_j(self.cfg[f'cartridge_pre_insertion_new_{cartridge_number}'])       
            self.robot.open_gripper()
            self.robot.move_robot_j(self.cfg[f'cartridge_pre_insertion_new_{cartridge_number}']) 
            self.robot.move_robot_j(self.cfg[f'cartridge_prepare_for_insertion_{cartridge_number}'])
            self.robot.move_robot_j(self.cfg[f'cartridge_midwaypoint_to_prepare_for_insertion_{cartridge_number}']) 
            self.robot.move_robot_j(self.cfg[f'cartridge_adjust_for_insertion_{cartridge_number}'])
            self.robot.move_robot_j(self.cfg['midway_robot_left'])
            self.robot.move_robot_j(self.cfg['start_joints_robot_left'])
            self.robot.move_robot_j(self.cfg['start_joints_centre'])
            print("[INFO] Cartridge inserted... ")
            return 
        except:
            print(f'[ERROR] Cartridge {cartridge_number} is not available.')
            self.camera.stop_streaming()
            exit()

    def remove_cartridge_from_quantos(self, cartridge_number = 1):
        """
        Removes the cartridge from quantos. It terminates the program if the front door of quantos is closed in order to avoid potential collisions. 
        """
        self.check_quantos_door_position()
        try:
            print("[INFO] Robot removing cartridge from quantos ... ")
            self.robot.move_robot_j(self.cfg['start_joints_robot_left'])
            self.robot.move_robot_j(self.cfg['midway_robot_left'])
            self.robot.move_robot_j(self.cfg[f'cartridge_adjust_for_insertion_{cartridge_number}'])
            self.robot.move_robot_j(self.cfg[f'cartridge_midwaypoint_to_prepare_for_insertion_{cartridge_number}'])  
            self.robot.move_robot_j(self.cfg[f'cartridge_prepare_for_insertion_{cartridge_number}'])  
            self.robot.move_robot_j(self.cfg[f'cartridge_insertion_new_{cartridge_number}']) 
            self.robot.move_robot_j(self.cfg[f'cartridge_pre_insertion_new_{cartridge_number}'])   
            self.robot.close_gripper()
            self.robot.move_robot_j(self.cfg[f'cartridge_pre_insertion_new_{cartridge_number}']) 
            self.robot.move_robot_j(self.cfg[f'cartridge_prepare_for_insertion_{cartridge_number}'])
            self.robot.move_robot_j(self.cfg[f'cartridge_midwaypoint_to_prepare_for_insertion_{cartridge_number}']) 
            self.robot.move_robot_j(self.cfg[f'cartridge_adjust_for_insertion_{cartridge_number}'])
            self.robot.move_robot_j(self.cfg['midway_robot_left'])
            self.robot.move_robot_j(self.cfg['start_joints_robot_left'])
            self.robot.move_robot_j(self.cfg['start_joints_centre'])
            return
        except:
            print(f'[ERROR] Cartridge {cartridge_number} is not available.')
            self.camera.stop_streaming()
            exit()
    def return_cartridge_to_holder(self, cartridge_number = 1):
        """
        Returns the cartridge to its holder TODO To recognise automatically which cartridge was taken..
        """
        try:
            print("[INFO] Robot returning cartridge to holder ... ")
            self.robot.move_robot_j(self.cfg['start_joints_robot_right'])#
            self.robot.move_robot_j(self.cfg[f'above_cartridge_{cartridge_number}_in_holder'])
            self.robot.move_robot_j(self.cfg[f'returning_cartridge_{cartridge_number}_in_holder'])
            self.robot.move_robot_j(self.cfg[f'returning_cartridge_{cartridge_number}_in_holder_1'])
            self.robot.open_gripper()
            self.robot.move_robot_j(self.cfg[f'above_cartridge_{cartridge_number}_in_holder'])
            self.robot.move_robot_j(self.cfg['start_joints_robot_right'])
            self.robot.move_robot_j(self.cfg['start_joints_centre'])
            return
        except:
            print(f'[ERROR] Cartridge {cartridge_number} is not available.')
            self.camera.stop_streaming()
            exit()
    def pick_and_place_cartridge_in_quantos(self, cartridge_number= 1):
        """
        Picks and places a given cartridge into the quantos station. 
        Terminates program if the cartridge was not mounted.
        :param cartridge_number: and integer between 1 and 3 wchis represent the number of the cartridge.
        """
        self.pick_up_cartridge_from_holder(cartridge_number = cartridge_number)
        self.insert_cartridge_in_quantos(cartridge_number = cartridge_number)
        self.check_quantos_cartridge()
        return
    def pick_and_place_cartridge_in_holder(self, cartridge_number= 1):
        """
        Picks a cartrige from the quantos station and places it into its holder. 
        :param cartridge_number: and integer between 1 and 3 wchis represent the number of the cartridge.
        """
        self.remove_cartridge_from_quantos(cartridge_number = cartridge_number)
        self.return_cartridge_to_holder(cartridge_number = cartridge_number)
        return
	################### Vial Manipulation methods ######################################
    def vial_rack_to_pump(self, vial_number=1):
        """
        Moves a vial from the rack to the pump.
        :param vial_number: an integer which possible values go from 1 to 22 
        """
        try:
            self.robot.open_gripper_set_width(0.035)
            self.robot.move_robot_j(self.cfg['start_joints_robot_right'])
            if vial_number>16:
                self.robot.move_robot_j(self.cfg[f'v_to_p_pre'])
            self.robot.move_robot_j(self.cfg[f'v_to_p_{vial_number}_1'])
            self.robot.move_robot_j(self.cfg[f'v_to_p_{vial_number}_2'])
            self.robot.close_gripper()
            self.robot.move_robot_j(self.cfg[f'v_to_p_{vial_number}_3'])
            if vial_number>16:
                self.robot.move_robot_j(self.cfg[f'v_to_p_{vial_number}_1'])
            self.robot.move_robot_j(self.cfg[f'v_to_p_{vial_number}_4'])
            self.robot.move_robot_j(self.cfg[f'v_to_p_{vial_number}_5'])
            self.robot.move_robot_j(self.cfg[f'v_to_p_{vial_number}_6'])
            self.robot.open_gripper_set_width(0.04)
            self.robot.move_robot_j(self.cfg[f'v_to_p_{vial_number}_7'])
            return
        except:
            print(f'[ERROR] Vial {vial_number} not available.')
            self.camera.stop_streaming()
            exit()
    def vial_rack_to_ika(self, vial_number=1, ika_slot_number=1):
        """
        Moves a vial from the rack to the IKA station.
        :param vial_number: an integer which possible values go from 1 to 22 
        :param ika_slot_number: an integer which possible values go from 1 to 12
        """
        try:
            self.vial_rack_to_pump(vial_number=vial_number)
            self.robot.open_gripper_set_width(0.04)
            self.robot.move_robot_j(self.cfg[f'push_1']) 
            self.robot.move_robot_j(self.cfg["p_to_q_1"])
            self.robot.move_robot_j(self.cfg["p_to_rack_2"])
            self.robot.close_gripper()
            self.robot.move_robot_j(self.cfg["p_to_q_3"])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_1'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_2'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_3'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_4'])
            self.robot.open_gripper_set_width(0.03)
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_3'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_2'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_1'])
            self.robot.move_robot_j(self.cfg[f'push_1'])
            return
        except:
            print(f'[ERROR] Vial {vial_number} or IKA slot {ika_slot_number} not available.')
            self.camera.stop_streaming()
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
    
    def vial_ika_to_rack(self, ika_slot_number=1, vial_number=1):
        """
        Moves a vial from the ika station to the rack.
        :param vial_number: an integer which possible values go from 1 to 22 
        :param ika_slot_number: an integer which possible values go from 1 to 12
        """
        self.vial_ika_to_pump(ika_slot_number=ika_slot_number)
        self.vial_pump_to_rack(vial_number=vial_number)
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
    
    def vial_ika_to_pump(self, ika_slot_number=1):
        """
        Moves a vial from the IKA station to the vial holder of the pump.
        :param ika_slot_number: an integer which possible values go from 1 to 12
        """
        try:
            self.robot.move_robot_j(self.cfg[f'push_1'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_1'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_2'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_3'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_4'])
            self.robot.close_gripper()
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_3'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_2'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_1'])
            self.robot.move_robot_j(self.cfg["p_to_q_3"])
            self.robot.move_robot_j(self.cfg["p_to_rack_2"])
            self.robot.open_gripper_set_width(0.04)
            return
        except:
            print(f'[ERROR] IKA slot {ika_slot_number} not available.')
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
    
    def vial_quantos_to_pump(self):
        """
        Moves a vial from the quantos station to the vial holder of the pump.
        Terminates if the front door of the quantos station is closed in order to avoid potential collisions.
        """
        try:
            self.check_quantos_door_position()
            self.robot.move_robot_j(self.cfg['start_joints_robot_left'])
            self.robot.move_robot_j(self.cfg["p_to_q_4"])
            self.robot.move_robot_j(self.cfg["p_to_q_5"])
            self.robot.move_robot_j(self.cfg["p_to_q_6"])
            self.robot.move_robot_j(self.cfg["p_to_q_7"])
            self.robot.move_robot_j(self.cfg["p_to_q_8"])
            self.robot.move_robot_j(self.cfg["p_to_q_8_5"])
            self.robot.move_robot_j(self.cfg["p_to_q_9"])
            self.robot.move_robot_j(self.cfg["p_to_q_10_1"])
            self.robot.close_gripper()
            self.robot.move_robot_j(self.cfg["p_to_q_10_2"])
            self.robot.move_robot_j(self.cfg["p_to_q_10_3"])
            self.robot.move_robot_j(self.cfg["p_to_q_10_4"])
            self.robot.move_robot_j(self.cfg["q_to_p_3"])
            self.robot.move_robot_j(self.cfg["q_to_p_4"])
            self.robot.move_robot_j(self.cfg["q_to_p_5"])
            self.robot.move_robot_j(self.cfg["q_to_p_6"])
            self.robot.move_robot_j(self.cfg['start_joints_centre'])
            self.robot.move_robot_j(self.cfg[f'push_1'])
            self.robot.move_robot_j(self.cfg["p_to_q_3"])
            self.robot.move_robot_j(self.cfg["p_to_rack_2"])
            self.robot.open_gripper_set_width(0.04)
            self.robot.move_robot_j(self.cfg["p_to_q_1"])
            self.robot.move_robot_j(self.cfg[f'push_1'])
            return
        except:
            print(f'[ERROR] Terminating program.')
            self.camera.stop_streaming()
            exit()
    def vial_pump_to_rack(self, vial_number=1, from_home=False):
        """
        Moves a vial from the vial holder of the pump to the rack.
        :param vial_number: an integer which possible values go from 1 to 22 
        :param from_home: bool when set to True, the robot executes this method from its home position. When is set to False, the robot executes its movements from a position close to the pump.
        """
        try:
            if from_home:
                self.robot.move_robot_j(self.cfg[f'push_1'])
                self.robot.move_robot_j(self.cfg["p_to_q_3"])
                self.robot.move_robot_j(self.cfg["p_to_rack_2"])
            self.robot.close_gripper()
            self.robot.move_robot_j(self.cfg["p_to_rack_2"])
            self.robot.move_robot_j(self.cfg["p_to_q_3"])
            self.robot.move_robot_j(self.cfg[f'p_to_rack_1_1'])
            if vial_number>8 and vial_number<17:
                self.robot.move_robot_j(self.cfg[f'p_to_rack_{vial_number}_1'])
            if vial_number>16 and vial_number<23:
                self.robot.move_robot_j(self.cfg[f'p_to_rack_9_1'])
                self.robot.move_robot_j(self.cfg[f'p_to_rack_{vial_number}_1'])
            self.robot.move_robot_j(self.cfg[f'p_to_rack_{vial_number}_pre'])
            self.robot.move_robot_j(self.cfg[f'p_to_rack_{vial_number}_2'])
            self.robot.move_robot_j(self.cfg[f'p_to_rack_{vial_number}_3'])
            self.robot.open_gripper_set_width(0.03)
            self.robot.move_robot_j(self.cfg[f'p_to_rack_{vial_number}_2'])
            self.robot.move_robot_j(self.cfg[f'p_to_rack_{vial_number}_1'])
            self.robot.move_robot_j(self.cfg["push_1"])
            return
        except:
            print(f'[ERROR] Vial {vial_number} not available.')
            self.camera.stop_streaming()
            exit()

    def vial_pump_to_ika(self, ika_slot_number=1):
        """
        Moves a vial from the vial holder of the pump to a given IKA slot.
        :param ika_slot_number: an integer which possible values go from 1 to 12
        """
        try:
            self.robot.open_gripper_set_width(0.04)
            self.robot.move_robot_j(self.cfg[f'push_1']) 
            self.robot.move_robot_j(self.cfg["p_to_q_1"])
            self.robot.move_robot_j(self.cfg["p_to_rack_2"])
            self.robot.close_gripper()
            self.robot.move_robot_j(self.cfg["p_to_q_3"])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_1'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_2'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_3'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_4'])
            self.robot.open_gripper_set_width(0.035)
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_3'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_2'])
            self.robot.move_robot_j(self.cfg[f'p_to_ika_{ika_slot_number}_1'])
            self.robot.move_robot_j(self.cfg[f'push_1'])
            return
        except:
            print(f'[ERROR] IKA slot {ika_slot_number} not available.')
            self.camera.stop_streaming()
            exit()

    def vial_pump_to_quantos(self):
        """
        Moves a vial from the vial holder of the pump to the Quantos mettler station. 
        Terminates the program if the front door of the quantos station is closed to avoid potential collisions. 
        """
        try:
            self.check_quantos_door_position()
            self.robot.open_gripper_set_width(0.04)
            self.robot.move_robot_j(self.cfg[f'push_1'])
            self.robot.move_robot_j(self.cfg["p_to_q_1"])
            self.robot.move_robot_j(self.cfg["p_to_q_2"])
            self.robot.close_gripper()
            self.robot.move_robot_j(self.cfg["p_to_q_3"])
            self.robot.move_robot_j(self.cfg[f'push_1'])
            self.robot.move_robot_j(self.cfg['start_joints_centre'])
            self.robot.move_robot_j(self.cfg['start_joints_robot_left'])
            self.robot.move_robot_j(self.cfg["p_to_q_4"])
            self.robot.move_robot_j(self.cfg["p_to_q_5"])
            self.robot.move_robot_j(self.cfg["p_to_q_6"])
            self.robot.move_robot_j(self.cfg["p_to_q_7"])
            self.robot.move_robot_j(self.cfg["p_to_q_8_5"])
            self.robot.move_robot_j(self.cfg["p_to_q_8"])
            self.robot.move_robot_j(self.cfg["p_to_q_10"])
            self.robot.move_robot_j(self.cfg["p_to_q_11"])
            self.robot.open_gripper_set_width(0.04)
            self.robot.move_robot_j(self.cfg["p_to_q_10"])
            self.robot.move_robot_j(self.cfg["p_to_q_9"])
            self.robot.move_robot_j(self.cfg["p_to_q_8"])
            self.robot.move_robot_j(self.cfg["p_to_q_7"])
            self.robot.move_robot_j(self.cfg["p_to_q_6"])
            self.robot.move_robot_j(self.cfg["p_to_q_5"])
            self.robot.move_robot_j(self.cfg["p_to_q_4"])
            self.robot.move_robot_j(self.cfg['start_joints_robot_left'])
            self.robot.move_robot_j(self.cfg['start_joints_centre'])
            return
        except:
            print(f'[ERROR] Robot not available, terminating program...')
            self.camera.stop_streaming()
            exit()
    #### Poses to take pictures #########################################################
    def camera_to_rack(self,rack_number=1):
        """
        Takes a photo of a given rack.
        :param rack_number: The rack number is a integer which range go from 1 to 3.
        """
        try:
            self.robot.close_gripper()
            self.robot.move_robot_j(self.cfg["camera_2"])
            self.robot.move_robot_j(self.cfg["camera_3"])
            self.robot.move_robot_j(self.cfg[f'camera_rack_{rack_number}'])
            self.camera.save_picture(f'rack_{rack_number}')
            self.robot.move_robot_j(self.cfg["camera_3"])
            self.robot.move_robot_j(self.cfg["camera_2"])
            self.robot.move_robot_j(self.cfg['start_joints_centre'])
        except:
            print(f'[ERROR] Rack {rack_number} not available.')
            self.camera.stop_streaming()
            exit()
        
    def camera_to_rack_photos_on_the_way(self):
        """
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
            print(f'[ERROR] Robot not available.')
            self.camera.stop_streaming()
            exit()

	#####################################################################################	
    def push_pump(self): 
        """
        Pushes the vial holder of the pump.
        """
        self.robot.open_gripper()
        self.robot.move_robot_j(self.cfg[f'push_1'])
        self.robot.move_robot_j(self.cfg[f'push_2'])
        self.robot.move_robot_j(self.cfg[f'push_3'])
        self.robot.close_gripper()
        self.robot.move_robot_j(self.cfg[f'push_4'])
        return
    
    def pull_pump(self): 
        """
        Pulls the vial holder of the pump.
        """
        time.sleep(3)
        self.robot.move_robot_j(self.cfg[f'push_3'])
        self.robot.open_gripper()
        self.robot.move_robot_j(self.cfg[f'push_2'])
        self.robot.move_robot_j(self.cfg[f'push_1'])
        return
    



