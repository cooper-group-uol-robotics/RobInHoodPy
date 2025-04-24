from rob_in_hood import RobInHood, CameraCapper
from config.configuration import *
from datetime import datetime
import os
import time

def input_checker(station:RobInHood):
      
    while True:
        station._logger.warning(' Has the vial been removed and replaced?(y/n)')
        yn=input()
        if yn =='y' or yn =='Y':
            station._logger.info("Resuming workflow.")
            break
        elif yn == 'n' or yn == 'N':
            station._logger.warning("Please replace the cartridge.")
    return 


if __name__ == "__main__":
    logname="acid_test_1.2M" + datetime.now().strftime("%d_%m_%Y_")+"_log"
    station = RobInHood(logname + "_log", sim = False, vel = 0.05)


    i = 0

    while i < 4:

        station._logger.info(f"Making {i+1} sample repeat")

        station.hold_position()
        station._logger.info("priming line with HCL 1.2 M")
        station.pump_prime_dispense_tubing("1.2M HCl",cycle_number=2)
        station._logger.info("Priming line with water(DI)")
        station.pump_prime_dispense_tubing("Water(DI)",cycle_number=2)
        station._logger.info("Add water vial")
        input_checker(station=station)
        station.infuse_position()

        station.dispense_volume(10000, "Water(DI)")

        station.hold_position()

        i +=1
    

    # # station.hold_position()
    # # station._logger.info("Priming line with HCL 1.2 M")
    # # station.pump_prime_dispense_tubing("1.2M HCl",cycle_number=2)
    # station._logger.info("Priming line with Water(DI)")
    # station.pump_prime_dispense_tubing("Water(DI)",cycle_number=2)
    # station._logger.info("Add water vial")
    # input_checker(station=station)
    # station.infuse_position()
   
    # station.dispense_volume(10000, "Water(DI)")



    