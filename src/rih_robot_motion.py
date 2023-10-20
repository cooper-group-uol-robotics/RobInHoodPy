from frankx import Affine, LinearRelativeMotion, Robot, Gripper
from frankx_helpers import FrankxHelpers
import json
import time

def read_json_cfg(filename):
    # print("Reading json ... ")
    cfg_raw = ''
    with open(filename) as cfg:
        cfg_raw = cfg.read()
        # print(cfg_raw)
    return json.loads(cfg_raw)

###### Home ######
def go_home():
    # robot.open_gripper_set_width(width=0.035)
    robot.move_robot_j(cfg['start_joints'])
    return 

###### Cartridge Manipulation ######
def pick_up_cartridge_from_holder(cartridge_number = 1):
    robot.open_gripper_set_width(width=0.04)
    robot.move_robot_j(cfg['start_joints_robot_right'])
    robot.move_robot_j(cfg['midway_robot_right'])
    robot.move_robot_j(cfg['above_cartridge1_in_holder'])
    robot.move_robot_j(cfg['cartridge1_in_holder'])
    robot.close_gripper()
    robot.move_robot_j(cfg['above_cartridge1_in_holder'])
    robot.move_robot_j(cfg['start_joints_robot_right'])
    robot.move_robot_j(cfg['start_joints'])
    return 

def insert_cartridge_in_quantos():
    robot.move_robot_j(cfg['start_joints_robot_left'])
    robot.move_robot_j(cfg['midway_robot_left'])
    robot.move_robot_j(cfg['cartridge_midwaypoint_to_prepare_for_insertion'])  
    robot.move_robot_j(cfg['cartridge_prepare_for_insertion'])  
    robot.move_robot_j(cfg['cartridge_pre_insertion_new'])   
    robot.move_robot_j(cfg['cartridge_pre_insertion_new_align']) 
    robot.move_robot_j(cfg['cartridge_insertion_new']) 
    robot.move_robot_j(cfg['cartridge_force_insertion_new'])  
    robot.move_robot_j(cfg['cartridge_force_insertion_new2'])       
    robot.open_gripper_set_width(width=0.045)
    robot.move_robot_j(cfg['cartridge_pre_insertion_new'])  
    robot.move_robot_j(cfg['cartridge_midwaypoint_to_prepare_for_insertion'])
    robot.move_robot_j(cfg['midway_robot_left'])
    return 

def remove_cartridge_from_quantos():
    robot.move_robot_j(cfg['start_joints_robot_right']) 
    robot.move_robot_j(cfg['start_joints_robot_left'])  
    robot.move_robot_j(cfg['midway_robot_left']) 
    robot.move_robot_j(cfg['cartridge_midwaypoint_to_prepare_for_insertion'])  
    robot.move_robot_j(cfg['cartridge_prepare_for_insertion'])          
    robot.move_robot_j(cfg['cartridge_insertion_newu'])   
    robot.close_gripper()
    robot.move_robot_j(cfg['cartridge_pre_insertion_new'])  
    robot.move_robot_j(cfg['cartridge_midwaypoint_to_prepare_for_insertion'])
    # robot.move_robot_j(cfg['cartridge_adjust_for_insertion'])
    robot.move_robot_j(cfg['midway_robot_left'])
    robot.move_robot_j(cfg['start_joints_robot_left'])
    robot.move_robot_j(cfg['start_joints'])
    return

def return_cartridge_to_holder(cartridge_number = 1):
    robot.move_robot_j(cfg['start_joints_robot_right'])    
    robot.move_robot_j(cfg['midway_robot_right'])
    robot.move_robot_j(cfg['above_cartridge1_in_holderu'])
    robot.move_robot_j(cfg['above_cartridge1_in_holder'])
    robot.move_robot_j(cfg['drop_cartridge_align1'])    
    robot.move_robot_j(cfg['drop_cartridge1'])
    robot.open_gripper_set_width(width=0.045)
    robot.move_robot_j(cfg['above_cartridge1_in_holder'])
    robot.move_robot_j(cfg['midway_robot_right'])
    return

###### Vial Manipulation ######

def pick_up_vial_from_wall_rack(vial_number=2):
    robot.move_robot_j(cfg['start_joints_robot_right'])
    robot.move_robot_j(cfg['midway_robot_right'])
    robot.open_gripper_set_width(width=0.03)
    # robot.move_robot_j(cfg['move_robot_close_to_rack'])
    robot.move_robot_j(cfg['post_grasp_vial'])

    robot.move_robot_j(cfg['pre_grasp_vial_1'])
    robot.move_robot_j(cfg["grasp_vial_1"])
    robot.close_gripper()
    robot.move_robot_j(cfg['pre_grasp_vial_1'])    
    robot.move_robot_j(cfg['post_grasp_vial'])
    return

def take_vial_to_pump():
    robot.move_robot_j(cfg['midway_robot_left'])
    robot.move_robot_j(cfg['start_joints_robot_left'])   
    robot.move_robot_j(cfg['start_joints_robot_right'])    
    robot.move_robot_j(cfg['midway_robot_right'])   
    robot.move_robot_j(cfg["midway_to_pump"])
    robot.move_robot_j(cfg["dispense_preload"])
    robot.move_robot_j(cfg["dispense_preload_align"])    
    robot.move_robot_j(cfg["load_dispense"])
    robot.open_gripper_set_width(width=0.05)
    return


def push_vial_pump_holder():
    robot.move_robot_j(cfg["dispense_preload"])
    robot.move_robot_j(cfg["midway_to_pump"])
    robot.move_robot_j(cfg["pre_push_dispense_midway"])  

    robot.move_robot_j(cfg["pre_push_dispense_pre_grasp"])
    robot.move_robot_j(cfg["pre_push_dispense_grasp"])
    robot.close_gripper()    
    robot.move_robot_j(cfg["push_dispense"])
    return
    
def pull_vial_pump_holder():
    robot.move_robot_j(cfg["pull_dispense"])
    robot.open_gripper_set_width(width=0.045)    
    robot.move_robot_j(cfg["pre_push_dispense_grasp"])
    robot.move_robot_j(cfg["pre_push_dispense_pre_grasp"])
    robot.move_robot_j(cfg["pre_push_dispense_midway"])        
    return

def pickup_vial_from_pump():
    robot.move_robot_j(cfg["dispense_preload_align"])   
    robot.move_robot_j(cfg["grasp_vial_in_pump_holder"])   
    robot.close_gripper()
    robot.move_robot_j(cfg["dispense_preload"])
    robot.move_robot_j(cfg["midway_to_pump"])
    robot.move_robot_j(cfg['midway_robot_right'])    
    return

def take_vial_to_quantos():
    robot.move_robot_j(cfg['start_joints_robot_right'])

    robot.move_robot_j(cfg['start_joints_robot_left'])
    robot.move_robot_j(cfg['midway_robot_left'])
    robot.move_robot_j(cfg['midway_robot_left_lower'])
    robot.move_robot_j(cfg['pre_pre_pre_vial_quantos'])
    robot.move_robot_j(cfg['pre_pre_vial_quantos'])
    robot.move_robot_j(cfg['pre_vial_quantos'])
    robot.move_robot_j(cfg['vial_quantos'])    
    robot.open_gripper_set_width(width=0.035)   
    robot.move_robot_j(cfg['grasp_vial_quantos'])      
    robot.close_gripper()
    robot.move_robot_j(cfg['pre_vial_quantosu'])
    robot.move_robot_j(cfg['pre_pre_vial_quantos'])
    robot.move_robot_j(cfg['pre_pre_pre_vial_quantos'])
    robot.move_robot_j(cfg['midway_robot_left_lower'])
    robot.move_robot_j(cfg['midway_robot_left'])
    return

def take_vial_to_ika_plate():
    robot.move_robot_j(cfg['midway_robot_right_lower'])
    robot.move_robot_j(cfg['vial_above_ika_plate'])     
    robot.move_robot_j(cfg['vial_ika_plate'])       
    robot.open_gripper_set_width(width=0.045)   
    robot.move_robot_j(cfg['vial_ika_plate'])    
    robot.close_gripper()       
    robot.move_robot_j(cfg['vial_above_ika_plate'])  
    return

def return_vial_to_wall_rack(vial_number=1):
    # robot.move_robot_j(cfg['vial_ika_plate'])    
    # robot.close_gripper()       
    robot.move_robot_j(cfg['vial_above_ika_plate'])  
 
    robot.move_robot_j(cfg['midway_robot_right'])
    robot.move_robot_j(cfg['above_vials'])

    robot.move_robot_j(cfg['above_rack_1_right'])

    robot.move_robot_j(cfg['pre_grasp_vial_1'])
    robot.move_robot_j(cfg['align_vial_1d'])

    robot.move_robot_j(cfg['drop_vial1d'])

    robot.open_gripper_set_width(width=0.045) 
    robot.move_robot_j(cfg['pre_grasp_vial_1'])

    robot.move_robot_j(cfg['midway_robot_right'])    
    robot.move_robot_j(cfg['start_joints_robot_right'])
    return    

def load_vial_quantos():       
    robot.move_robot_j(cfg['start_joints_centre'])
    robot.move_robot_j(cfg['midway_robot_left'])
    robot.move_robot_j(cfg["quantos_set_up"])
    robot.move_robot_j(cfg["quantos_vertical_level"])
    robot.move_robot_j(cfg["quantos_prep_vial_release"])
    


if __name__ == '__main__':
    robot = FrankxHelpers("172.16.0.2")
    robot.reset_robot()
    # robot.set_dynamic_rel(0.1)
    cfg = read_json_cfg('rih_robot_motion_positions.json')
    robot.open_gripper_set_width(width=0.035)
    go_home()

    for i in range(10):
        print(i)
        go_home()
    # # ########## Cartridge Manipulation    
        pick_up_cartridge_from_holder(cartridge_number = 1)
        insert_cartridge_in_quantos()
        # remove_cartridge_from_quantos()
        # return_cartridge_to_holder(cartridge_number=1)

    # ########## Vial Manipulation      
        go_home() 
        pick_up_vial_from_wall_rack(vial_number=1)
        take_vial_to_quantos()
        #load_vial_quantos()
        take_vial_to_pump()
        push_vial_pump_holder()
        # # time.sleep(0.1)
        pull_vial_pump_holder()
        pickup_vial_from_pump()

        #take_vial_to_ika_plate()
        return_vial_to_wall_rack(vial_number=1)
        robot.recover_from_errors()

    # # ########## Cartridge Manipulation
        remove_cartridge_from_quantos()
        return_cartridge_to_holder(cartridge_number=1)
        robot.move_robot_j(cfg['start_joints_robot_right']) 


