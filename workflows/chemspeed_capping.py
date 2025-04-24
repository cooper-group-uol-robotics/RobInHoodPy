import sys
import os

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__))+'/..')


import math
import time
from rob_in_hood import RobInHood
from config.configuration import *


vials={     1:['water_chempseed_2','3'],
           2:['water_chemspeed_2','3'],
           3: ['water_chemspeed_2', '3'],
           4: ['water_chemspeed_2', '3'],
        
           5: ['ethanol_chemspeed_2', '4'],
           6: ['ethanol_chemspeed_2', '4'],
           13: ['ethanol_chemspeed_2', '4'],
           14: ['ethanol_chemspeed_2', '4'],
           
           9: ['acetone_chemspeed_2', '5'],
           10: ['acetone_chemspeed_2', '5'],
           11: ['acetone_chemspeed_2', '5'],
           12: ['acetone_chemspeed_2', '5']  
           }


vials_2 = {1:['water_chempseed_appendtest','3'],}

def control_experiment(step_by_step=False):
    station=RobInHood("14102024_chemspeed_capping_log", sim=False,vel=0.05)
    station.robot.open_gripper()
    #input()
    station.hold_position()
    for t in range(0,40):
        for i in [1,2,3,4,5,6,13,14,9,10,11,12]:    
            #input('run?')
            station.vial_rack_to_pump(i)
            station.shut_door()
            station.quantos.zero()
            time.sleep(1)
            station.quantos.open_front_door()
            station.quantos.open_side_door()
            station.vial_pump_to_quantos()
            station.shut_door()
            #station.log_weight(vials[i][0],str(i), str(station.take_weight()))
            #station.log_weight(vials[i][0],str(i), str(station.take_weight()))
            #station.log_weight(vials[i][0],str(i), str(station.take_weight()))
            station.quantos.open_front_door()
            station.quantos.open_side_door()
            station.vial_quantos_to_rack(i)
        station.timer.set_timer(hours=1,min=0,sec=0)
        station.timer.start_timer()
    station.go_home()



def just_weight():
    station=RobInHood("09072024_chemspeed_capping_log", sim=False,vel=0.05)
    
    for i in [1,2,3,4]:

        input("clear balance")
        station.quantos.close_front_door()
        station.quantos.close_side_door()
        station.quantos.tare()
        station.quantos.zero()
        station.quantos.open_front_door()
        station.quantos.open_side_door()
        input("place vial")
        station.quantos.close_front_door()
        station.quantos.close_side_door()
        station.log_weight(vials_2[i][0],str(i), str(station.take_weight()))
        station.log_weight(vials_2[i][0],str(i), str(station.take_weight()))
        station.log_weight(vials_2[i][0],str(i), str(station.take_weight()))
        station.quantos.open_front_door()
        station.quantos.open_side_door()
        input("remove vial")
    
    station.quantos.tare()


def tare_check():
    station=RobInHood("18062024_tare_check", sim=False,vel=0.05)
    station.quantos.close_front_door()
    station.quantos.close_side_door()
    print("quantos tare")
    print(station.quantos.tare())

def zero_check():
    station=RobInHood("18062024_tare_check", sim=False,vel=0.05)
    station.quantos.close_front_door()
    station.quantos.close_side_door()
    print("quantos tare")
    print(station.quantos.zero())

def append_test():
    station=RobInHood("18062024_tare_check", sim=False,vel=0.05)
    station.quantos.open_front_door()
    station.quantos.open_side_door()
    station.check_quantos_door_position()

if __name__ == "__main__":
    #ero_check()
    #just_weight()
    #tare_check()
    control_experiment()
    #append_test()
   # append_test()