
#from rob_in_hood import RobInHood
#from config.configuration import *
from datetime import datetime
import os
import time
#from drivers.OnlyArduino import Arduino
from pylabware import XCalibur



def samples_rack_to_ika(vials_order:list, logname=datetime.now().strftime("%d_%m_%Y_")+"_log" ):
    station = RobInHood(logname+"_log", sim=False,vel=0.05)
    station.robot.open_gripper()
    station.robot.close_gripper()
    station.robot.open_gripper()
    
    for vial_pos in vials_order:
        station.vial_rack_to_ika(vial_pos)
    return
def set_down(logname=datetime.now().strftime("%d_%m_%Y")):
    """"""

    #TODO add cleaning vial method
    station = RobInHood(logname + "_log", sim = False, vel = 0.05)
    
    station._logger.info("Cleaning up after experiment")

    
    station._logger.info("Removing quantos cartridge(if needed")
    #removing quantos cartridge left in quantos
    for sample in reversed(station.sample_dict):
       if station.sample_dict[sample]["solid"] != "None":
            station.check_quantos_door_position()
            unlock = station.quantos.unlock_dosing_head_pin()
            if not (unlock['success']==True):
                station._logger.error("Dosing pin did not unlock!")
                station.camera.stop_streaming()
                exit()

            cartridge_pos = station.quantos_dict[station.sample_dict[sample]["solid"]]
            
            station._logger.info(f"Returning cartridge to position {cartridge_pos}")
            station.remove_cartridge_from_quantos(cartridge_pos)
            break
       else: 
           print(station.sample_dict[sample]["solid"])
           station._logger.debug(f"{station.sample_dict[sample]} has no solid so no need to unload")

    #washes the dispense tubing with water 
    #removing last primed solvent from dispense pump by priming the pump with air  
    station.hold_position()
    station.pump_prime_dispense_tubing("Water(DI)")
    station.pump_prime_dispense_tubing("Air")

    #purging all tubing lines in filt_machine with air
    input("Please pour 9 ml DI water down the funnel")
    station.filt_machine.wash_receiving_flask_pre(wash_volume=9000)
    station.filt_machine.purge_tubing_lines()

def cleaning_filtering_pump(logname=datetime.now().strftime("%d_%m_%Y")):
    #TODO add cleaning vial method
    station = RobInHood(logname + "_log", sim = False, vel = 0.05)


def unprime_lines(logname=datetime.now().strftime("%d_%m_%Y")):
    """
    Unprimes all reagent tubing for the dispense station pump. 
    Uses air from the air port to push tubing back into storage vessels.
    """
    station = RobInHood(logname+"_log", sim=False,vel=0.05)
    for solvent in station.dispense_dict:
        if not solvent in ["Dispense", "Air", "Waste"] and not solvent == "None":
            station.pump_expel_reagent_tubing(chemical=solvent)



def photograph_samples(logname=datetime.now().strftime("%d_%m_%Y"), samples=[7, 8, 9, 10, 11, 12], path="",dataset_name=""):
    """
    Photographs samples and saves them in the specified path
    """
    station=RobInHood(logname+"_log", sim=False,vel=0.05)
    station.robot.open_gripper()
 
    station.open_lightbox()
   
    for sample_number in samples:
       
        liquid_name = station.sample_dict[sample_number-7]["liquid"]
        solid_name = station.sample_dict[sample_number-7]["solid"]
        station.vial_rack_to_pump(vial_number=sample_number)
        
        station.vial_pump_to_lightbox()
        station.close_lightbox()
        station.light_on()
        #station.save_picture_from_lightbox(solid_name=solid_name,dye_name=liquid_name,path=path)
        station.light_off()
        station.open_lightbox()
        station.vial_lightbox_to_pump()
        station.vial_pump_to_rack(vial_number=sample_number)
    station.close_lightbox()
    porous=False
    #print(path)
    #print(dataset_name)
    #print("The material is porous.")
    return porous


def dispense_dropwise(volume:float, chemical:str = "Water(DI)" , speed: int =11):

   

    station.pump.set_predefined_speed(speed)

    print(station.pump.get_max_velocity())

    station.dispense_volume(volume, chemical)


def filter_samples(station:RobInHood):
    
    input("pour 9ml water")
    station.filt_machine.filter_setup(volume_filtered=9000, wait_time=600, stepping=False)
    
    input("place vial to be filtered")
    station.filt_machine.filter_vial(volume_filtered=9000, vacuum_time = 2000, stepping=False)

    input("do cleaning")

    station.filt_machine.clean(volume_filtered=9000,wash_solvent="Water(DI)", stepping=False)


def prime_lines(logname=datetime.now().strftime("%d_%m_%Y")):
    """
    Primes all reagent tubing for the pumps used in both the dispensing station and filtration station.
    Does not prime unused tubing and does not prime non reagent tubing.
    """
    station = RobInHood(logname+"_log", sim=False,vel=0.05)
    for solvent in station.dispense_dict:
        if not solvent in ["Dispense", "Air", "Waste"] and not solvent == "None":
            station.pump_prime_reagent_tubing(solvent)

    for solvent in station.filt_dict:

        if not solvent in ["Receiving_Flask", "Priming_Waste", "Waste", "Output_Needle", "Air"] and not solvent == "None": 
            station.filt_machine.prime_system_solvent(solvent)


def quantos_logic(station:RobInHood, solid_name):

    print(solid_name)    
    if solid_name == 'None' or solid_name == "none":
        
        solid_name=None
    

    if solid_name != None:   
            cartridge_pos = station.quantos_dict[solid_name]
            print(solid_name)
            print(cartridge_pos)
            if station._cartridge_in_quantos == None:
                station._logger.info(f"No cartridge loaded on quantos - placing cartridge {cartridge_pos}.")
                station.pick_and_place_cartridge_in_quantos(cartridge_pos)

            elif station._cartridge_in_quantos != cartridge_pos and station._cartridge_in_quantos != None:
                station._logger.info(f"Cartridge on quantos is from position {station._cartridge_in_quantos} - removing it.")
                station.remove_cartridge_from_quantos(station._cartridge_in_quantos)
                
                station._logger.info(f"Placing cartridge at position {cartridge_pos}")
                station.pick_and_place_cartridge_in_quantos(cartridge_pos)
            
            elif station._cartridge_in_quantos == cartridge_pos:
                station._logger.info(f"Requested cartridge at position: {station._cartridge_in_quantos} already on quantos no need to load it again.")

            else: 
                raise Exception("Unhandled cartridge loading logic")


def make_pump_test_sample(station:RobInHood, vol:int, number_samples:int, chemical:str):
    i = range(number_samples)
    for n in i:
        print(n)
        while True:
            inp = input("Is a vial inserted into the holder")
            if inp == 'y' or inp == 'Y':
                print("Proceeding")
                break
        
        station.infuse_position()

        station.acid_dispense_dropwise(vol = vol, chemical = chemical, speed=20)

        station.hold_position()









if __name__ == "__main__":

    print(os.getcwd())

    #logname= datetime.now().strftime("%d_%m_%Y_")+"_log"
    #station = RobInHood(logname + "_log", sim = False, vel = 0.05)

