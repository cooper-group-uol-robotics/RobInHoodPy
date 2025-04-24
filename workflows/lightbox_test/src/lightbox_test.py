import sys
import os

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__))+'/..')

import math
import time
from rob_in_hood import RobInHood
from config.configuration import *


def test_lightbox():
    station=RobInHood("15102024_lightbox_log", sim=False,vel=0.05)
    station.robot.open_gripper()
    #station.close_lightbox()##
    #station.close_lightbox()##
    station.open_lightbox()
    names={7:"10ppm",8:"8ppm",9:"6ppm",10:"4ppm",11:"2ppm"}
    for i in [7,8,9,10,11]:
        #station.vial_rack_to_pump(vial_number=i)
        
        
        input("Put vial: "+str(i))
        #station.vial_pump_to_lightbox()
        station.close_lightbox()
        station.light_on()
        station.save_picture_from_lightbox(solid_name="sample_"+str(i),dye_name="dye6_"+names[i])
        station.light_off()
        station.open_lightbox()
        input("Remove vial: "+str(i))
    station.close_lightbox()

def test_lightbox_frames():
    station=RobInHood("15102024_lightbox_log", sim=False,vel=0.05)
    station.robot.open_gripper()
    #station.close_lightbox()
    i=6
    station.vial_rack_to_pump(vial_number=i)
    station.open_lightbox()
    station.vial_pump_to_lightbox()
    station.close_lightbox()
    station.light_on()
    station.save_picture_from_lightbox(solid_name="solid"+str(i),dye_name="dye"+str(i))
    station.light_off()
    station.open_lightbox()
    station.vial_lightbox_to_pump()
    station.close_lightbox()
    station.vial_pump_to_rack(vial_number=i)
    
    return

def test_capping_failure():
    station=RobInHood("15102024_capping_failure_test_log", sim=False,vel=0.05)
    station.robot.open_gripper()
    input('Put a capped vial.')
    station.check_capping()
    input('Put an uncapped vial.')
    station.check_capping()
    return
def test_rack_to_pump_vials(vial_number=1):
    station=RobInHood("15102024_lightbox_log", sim=False,vel=0.05)
    station.robot.open_gripper()
    station.hold_position()
    station.vial_rack_to_pump(vial_number=vial_number)
    station.vial_pump_to_rack(vial_number=vial_number)
    return

if __name__ == "__main__":
    if sys.argv[1]=='take_photos':
        test_lightbox()
    elif sys.argv[1] == 'test_capping_failure':
        test_capping_failure()
    elif sys.argv[1] == 'test_lightbox_frames':
        test_lightbox_frames()
    elif sys.argv[1] == 'test_rack_to_pump_vials':
        test_rack_to_pump_vials(vial_number=12)
    else:
        print("Not a valid argument.")