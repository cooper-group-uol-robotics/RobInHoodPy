from rob_in_hood import RobInHood, CameraCapper
from config.configuration import *
from datetime import datetime
import os
import time

###Script for cleaning the TECAN XCalibur syringe pump using a weak base - weak acid - water clean as described in the manual ###

def input_checker(station:RobInHood):
    """
    Waits for user input before continuing the programme
    """
    while True:
        station._logger.warning(' Has the container been removed and replaced?(y/n)')
        yn=input()
        if yn =='y' or yn =='Y':
            station._logger.info("Resuming workflow.")
            break
        elif yn == 'n' or yn == 'N':
            station._logger.warning("Please replace the cartridge.")
    return 


def expel_reagents(station:RobInHood, vol: float = 6000):
    """
    Uses air to push liquids in the reagent tubes back into their bottles.
    """

    for solvent in station.dispense_dict:
        if not solvent in ["Dispense", "Air","NotInUse" ] and not solvent == "None":
            station.pump_expel_reagent_tubing(chemical=solvent, expel_volume=vol)

def reagent_wash_cycle(station:RobInHood, wash_solvent:str, vol: float = 6000):
    """Washes all tubing lines with the exception of Air, Waste and Water(DI) - reagent and dispense"""
    
    counter = 0 #counter for soaking step as it only needs to be done once as it is for the syringe not the tubing lines
    
    station._logger.info(f"Priming the wash line with {wash_solvent} from port {station.dispense_dict[wash_solvent]}")
    station.pump.dispense(volume = vol,source_port = station.dispense_dict[wash_solvent], destination_port= station.dispense_dict["Waste"])   
    
    for solvent in station.dispense_dict:
        if not solvent in ["Dispense", "Air", "Waste", "Water(DI)", "WASH_SOLV", "NotInUse"] and solvent != None:
            station._logger.info(f"Now washing solvent {solvent} on port {station.dispense_dict[solvent]}")
            station._logger.info(f"Solvent is: {solvent}")
               
            station.pump.dispense(volume = vol,source_port = station.dispense_dict[wash_solvent], destination_port= station.dispense_dict[solvent])

            if counter == 0 and wash_solvent != "Air":
                station._logger.info("Pausing for 10 minutes with cleaning solution in the syringe")
                station.pump.set_valve_position(requested_position=station.dispense_dict[wash_solvent])
                station.pump.move_plunger_absolute(3000)
                time.sleep(600)
                station.pump.set_valve_position(requested_position=station.dispense_dict["Waste"])
                station.pump.move_plunger_absolute(0)
                station._logger.info("10 minute wait completed - resuming wash")
                counter = 1

        elif solvent == "Dispense":
            #cleaning the dispense tubing which has a lower volume
            #dispense tube volume is approximately 1 mL
            station._logger.info(f"Priming dispense line with wash solvent from port: {station.dispense_dict[solvent]}")
            station.pump.dispense(volume = 4000,source_port = station.dispense_dict[wash_solvent], destination_port= station.dispense_dict[solvent])
      

def just_syringe_wash(station:RobInHood, wash_solvent:str):
    station._logger.info("Pausing for 10 minutes with cleaning solution in the syringe")
    station.pump.set_valve_position(requested_position=station.dispense_dict[wash_solvent])
    station.pump.move_plunger_absolute(3000)
    time.sleep(600)
    station.pump.set_valve_position(requested_position=station.dispense_dict["Waste"])
    station.pump.move_plunger_absolute(0)
    station._logger.info("10 minute wait completed - resuming wash")



if __name__ == "__main__":
    
    logname="dispense_pump_cleaning" + datetime.now().strftime("%d_%m_%Y_")+"_log"
    station = RobInHood(logname + "_log", sim = False, vel = 0.05)
    

    just_syringe_wash(station=station, wash_solvent="Water(DI)")

    # # station._logger.info("Flushing solvents back into their reagent bottles")      
    

    # # station._logger.info("Remove reagent bottles - and check condition of lids, empty and replace waste container")
    # # input_checker(station=station)

    
    # # station._logger.info("0.1 M NaOH base wash cycle")
    # # station._logger.info(f"PLease connect 0.1 M NaOH to port: {wash_solvent}")
    # # input_checker(station=station)
    # # reagent_wash_cycle(station=station, wash_solvent="WASH_SOLV")
    

    # input_checker(station=station)

    # station.pump_prime_reagent_tubing("Water(DI)")
    # station._logger.info("starting water rinse")
    # station._logger.info(f"PLease connect Water (DI)")
    # input_checker(station=station)
    # reagent_wash_cycle(station=station, wash_solvent= "Water(DI)", vol=20000)

    # # station._logger.info("0.1 M HCl acid wash cycle") 
    # # station._logger.info(f"PLease connect 0.1 M HCl to port: {wash_solvent}")
    # # input_checker(station=station)
    # # reagent_wash_cycle(station=station, wash_solvent="WASH_SOLV")

    # # station._logger.info("Water rinse")
    # # station._logger.info(f"PLease connect Water (DI) to port: {wash_solvent}")
    # # input_checker(station=station)
    # # reagent_wash_cycle(station=station, wash_solvent= "WASH_SOLV", vol=10000)

    # station._logger.info("Air clear")
    
    # reagent_wash_cycle(station=station, wash_solvent= "Air", vol=10000)
    





            
            



        