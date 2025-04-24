import sys
import math
import time
from rob_in_hood import RobInHood
from utils.inspector_hood import RobInHoodInspector
from config.configuration import *
from datetime import datetime

# datetime object containing current date and time


def prepare_samples(sample_list:list,capping=False,file_name = "results.txt",logname=datetime.now().strftime("%d_%m_%Y")):
    """
    Preparation steps for dye experiment each sample gets 6 mg of specified solid and 9 ml of specified liquid.

    file_name - file_name for results file
    sample_dict - dictionary of samples to be prepared

    """
    station=RobInHood(logname+"_log", sim=False,vel=0.05)
    
    #unpacking sample information from sample_dictionary
    for sample_number in sample_list:
        liquid_name = station.sample_dict[sample_number]["liquid"]
        liquid_volume = station.sample_dict[sample_number]["volume (ml)"] *1000 #all dispense steps in uL
        solid_name = station.sample_dict[sample_number]["solid"]
        
        if solid_name== 'None':
            solid_name=None
        solid_mass = station.sample_dict[sample_number]["mass (mg)"]
        vial_pos = station.sample_dict[sample_number]["vial"]
        
        station.hold_position()
        station.pump_prime_dispense_tubing(liquid_name)
        #TODO move this inside of robinhood class
        
        if solid_name != None:
            cartridge_pos = station.quantos_dict[solid_name] #cartridge position of material specified in material name
            if station._cartridge_in_quantos == None:
                station._logger.info(f"[INFO] No cartridge loaded on quantos - placing cartridge {cartridge_pos}.")
                station.pick_and_place_cartridge_in_quantos(cartridge_pos)

            elif station._cartridge_in_quantos != cartridge_pos and station._cartridge_in_quantos != None:
                station._logger.info(f"[INFO] Cartridge on quantos is from position {station._cartridge_in_quantos} - removing it.")
                station.remove_cartridge_from_quantos(station._cartridge_in_quantos)
                
                station._logger.info(f"[INFO] Placing cartrige at position {cartridge_pos}")
                station.pick_and_place_cartridge_in_quantos(cartridge_pos)
            
            elif station._cartridge_in_quantos == cartridge_pos:
                print(f"[INFO] Requested cartridge at position: {station._cartridge_in_quantos} already on quantos no need to load it again.")

            else: 
                raise Exception("Unhandled cartridge loading logic")


            station.vial_rack_to_quantos(vial_pos)
            mass = station.quantos_dosing(solid_mass)
            try:
                station.record_weight(sample_name = str(sample_number) + solid_name, file_name= solid_name+"_"+file_name ,weight =mass )
            except TypeError as te:
                station._logger.error("Mass measurement failed")

            ###removing vial
            station.vial_quantos_to_pump()
            
        else:
            station.vial_rack_to_pump(vial_number=vial_pos)
            station._logger.info("No solid selected")
        
        station.infuse_position()
        

        station.dispense_volume(liquid_volume,liquid_name)
        station.hold_position()
        station.vial_pump_to_rack(vial_pos)

    station.pump_prime_dispense_tubing("Water(DI)") # Wash the dispense tubing at the end of the process
    station.pump_prime_dispense_tubing("Air")
    
    return

def prepare_nmof_samples(station: RobInHood, filename: str = "results.txt", stirr_time:int = 240):
    """Sample preparation steps for NMOFs"""
    

    #unpacking sample information from sample_dictionary
    for sample_number in station.sample_dict:
        liquid_name = station.sample_dict[sample_number]["liquid"]
        liquid_volume = station.sample_dict[sample_number]["volume (ml)"] *1000 #all dispense steps in uL
        solid_name = station.sample_dict[sample_number]["solid"]
        solid_mass = station.sample_dict[sample_number]["mass (mg)"]
        vial_pos = station.sample_dict[sample_number]["vial"]
        meta = station.sample_dict[sample_number]["meta"] # used for dispense instruction

        #priming ahead of liquid dispense
        station.hold_position() 
        station.pump_prime_dispense_tubing(liquid_name)

        #Quantos logic
        if solid_name == 'None' or solid_name == "none":
        
            solid_name=None
    

        if solid_name != None:   
            cartridge_pos = station.quantos_dict[solid_name]
          
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

            station.vial_rack_to_quantos(vial_pos)
            mass = station.quantos_dosing(solid_mass)

            try:
                station.record_weight(sample_name = str(sample_number) + solid_name, file_name= solid_name + "_" +filename,weight =mass )
            except TypeError as te:
                station._logger.error("Mass measurement failed")

            ###removing vial
            station.vial_quantos_to_pump()

        else:
            #if no solid requested - it moves the vial directly to the dispensing station
            station.vial_rack_to_pump(vial_pos)
        
        station.infuse_position()

        if meta == "Dropwise":
            station.lightbox.stirr_on()
            station._logger.info("Beginning stirring")
            time.sleep(stirr_time-20)
            input("Is it dissolved?")
            station.dispense_dropwise(vol = liquid_volume, chemical= liquid_name)
            time.sleep(20)
            station._logger.info("Finishing stirring")
            station.lightbox.stirr_off()

        else:
            station.dispense_volume(vol = liquid_volume, chemical=liquid_name)
        
        station.hold_position()
        station.vial_pump_to_rack(vial_pos)
        


    

def stirr_samples(hours=23,min=59,sec=59,logname=datetime.now().strftime("%d_%m_%Y")):
    """
    Sets timer and stirrs for the specified time. 
    """
    station=RobInHood(logname+"_log", sim=False,vel=0.05)
   
    station.ika.set_speed(200)
    station.ika.start_stirring()
    station.timer.set_timer(hours=hours,min=min,sec=sec)
    station.timer.start_timer()
    station.ika.stop()
    return

def store_samples(vials_order:list,logname=datetime.now().strftime("%d_%m_%Y")):
    """
    Picks vials from the IKA plate and places them in their corresponding rack slots.
    """
    station=RobInHood(logname+"_log", sim=False,vel=0.05)
    for vial_pos in vials_order:
        station.vial_ika_to_rack(vial_pos)
    return

def samples_rack_to_ika(vials_order:list, logname=datetime.now().strftime("%d_%m_%Y")):
    station = RobInHood(logname+"_log", sim=False,vel=0.05)
    for vial_pos in vials_order:
        station.vial_rack_to_ika(vial_pos)
    return

def filter_samples(station:RobInHood,logname=datetime.now().strftime("%d_%m_%Y"),pouring_vial_number=1,fresh_vial_number=7, cleaning_vial_number=6):
    """
    Pouring_vial_number = vial position in the rack of the vial to be filtered
    fresh_vial_number = vial position in the rack of the vial where the filtrate will go
    cleaning_vial_number = index of the cleaning vial in the sample list 

    """
    station = RobInHood(logname+"_log", sim=False,vel=0.0)
    
    
   
    #######
    
    #making a cleaning vial to pour over the filter
    liquid_name = station.sample_dict[cleaning_vial_number]["liquid"]
    liquid_volume = station.sample_dict[cleaning_vial_number]["volume (ml)"] *1000 #all dispense steps in uL
    vial_pos = station.sample_dict[cleaning_vial_number]["vial"]
    
    station.hold_position()
    station.robot.open_gripper_set_width(0.03)
    station.pump_prime_dispense_tubing(liquid_name)
    station.vial_rack_to_pump(vial_number=vial_pos)
    station.infuse_position()
    station.dispense_volume(liquid_volume,liquid_name)
    station.hold_position()
    station.vial_pump_to_rack(vial_pos)

    #######
    station.quantos.close_front_door()
    station.robot.open_gripper()
    station.pick_up_filtering_catridge()
    station.place_pouring_cleaning_vial(vial_number=vial_pos)
    station.filt_machine.filter_setup(volume_filtered=9000, wait_time=600, stepping=False)
    station.remove_pouring_vial(vial_number=vial_pos)
    station.vial_decap(pouring_vial_number)
    station.place_pouring_vial()
    station.place_filtered_vial(fresh_vial_number) 
    station.filt_machine.filter_vial(volume_filtered=9000, vacuum_time = 2000, stepping=False)
    station.remove_filtered_vial(fresh_vial_number)
    station.remove_pouring_vial(pouring_vial_number)
    station.filt_machine.clean(volume_filtered=9000,wash_solvent="Water(DI)", stepping=False)
    station.quantos.open_front_door()
    station._logger.warning("Please replace the cartridge.")
    while True:
        station._logger.warning(' Has the cartridge been replaced?(y/n)')
        yn=input()
        if yn =='y' or yn =='Y':
            station._logger.info("Resuming workflow.")
            break
        elif yn == 'n' or yn == 'N':
            station._logger.warning("Please replace the cartridge.")
    return 

def photograph_samples(logname=datetime.now().strftime("%d_%m_%Y"), samples=[7,8,9,10,11,12], path="",dataset_name=""):
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
        #station.open_lightbox()
        station.vial_pump_to_lightbox()
        station.close_lightbox()
        station.light_on()
        station.save_picture_from_lightbox(solid_name=solid_name,dye_name=liquid_name,path=path)
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

def photograph_samples_no_solid(logname=datetime.now().strftime("%d_%m_%Y"), samples=[4,5], path="",dataset_name=""):
    """
    Photographs samples and saves them in the specified path - saves them with the name of the dataset plus the liquid name
    """
    station=RobInHood(logname+"_log", sim=False,vel=0.05)
    #station.robot.open_gripper()
    input(f"Photographing samples {dataset_name} ")

    for sample_number in samples:
        liquid_name = station.sample_dict[sample_number]["liquid"]
        solid_name = dataset_name
        sample_number = station.sample_dict[sample_number]["vial"]
        station.vial_rack_to_pump(vial_number=sample_number)
        station.open_lightbox()
        station.vial_pump_to_lightbox()
        station.close_lightbox()
        station.light_on()
        station.save_picture_from_lightbox(solid_name=solid_name,dye_name=liquid_name,path=path)
        station.light_off()
        station.open_lightbox()
        station.vial_lightbox_to_pump()
        station.vial_pump_to_rack(vial_number=sample_number)
        station.close_lightbox()
    porous=False
    print(path)
    print(dataset_name)
    
    return porous

def move_robot(logname=datetime.now().strftime("%d_%m_%Y")):
    station=RobInHood(logname+"_log", sim=False,vel=0.05)
    station.linear_test([-0.041982, 0.376051, 0.526305, 3.1116, 0.0, 0.0])


def prime_lines(station:RobInHood):
    """
    Primes all reagent tubing for the pumps used in both the dispensing station and filtration station.
    Does not prime unused tubing and does not prime non reagent tubing.
    """
  
    for solvent in station.dispense_dict:
        if not solvent in ["Dispense", "Air", "Waste"] and not solvent == "None":
            station.pump_prime_reagent_tubing(solvent)

    for solvent in station.filt_dict:

        if not solvent in ["Receiving_Flask", "Priming_Waste", "Waste", "Output_Needle", "Air"] and not solvent == "None": 
            station.filt_machine.prime_system_solvent(solvent)


def unprime_lines(logname=datetime.now().strftime("%d_%m_%Y")):
    """
    Unprimes all reagent tubing for the dispense station pump. 
    Uses air from the air port to push tubing back into storage vessels.
    """
    station = RobInHood(logname+"_log", sim=False,vel=0.05)
    for solvent in station.dispense_dict:
        if not solvent in ["Dispense", "Air", "Waste"] and not solvent == "None":
            station.pump_expel_reagent_tubing(chemical=solvent)



def set_down(logname=datetime.now().strftime("%d_%m_%Y")):
    """"""

    #TODO add cleaning vial method
    station = RobInHood(logname + "_log", sim = False, vel = 0.05)
    
    station._logger.info("Cleaning up after experiment")

    
    station._logger.info("Removing quantos cartridge (if needed)")
    #removing quantos cartridge left in quantos
    #TODO should not be iterating over the dictionary - should just do the last one that isn't None

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

def cleaning_pumps(logname=datetime.now().strftime("%d_%m_%Y")):
    #TODO add cleaning vial method
    station = RobInHood(logname + "_log", sim = False, vel = 0.05)
    station._logger.info("Cleaning up after experiment")
    station.hold_position()
    station.pump_prime_dispense_tubing("Water(DI)")
    station.pump_prime_dispense_tubing("Air")

    #purging all tubing lines in filt_machine with air
    input("Please pour 9 ml DI water down the funnel")
    station.filt_machine.wash_receiving_flask_pre(wash_volume=9000)
    station.filt_machine.purge_tubing_lines()
    
def categorise_samples(dataset_name=""):
    pass  

def demo():
    station = RobInHood("bestydemo" + "_log_please_erase_me", sim = False, vel = 0.05)
    station._logger.info("Running the best demo ever in the entire history of chemistry automation, money money gimme money.")
    for i in range(1,100):
        station.robot.open_gripper()
        station.vial_rack_to_pump(1)
        station.lightbox.stirr_on()
        time.sleep(10)
        station.lightbox.stirr_off()
        station.vial_pump_to_capper(to_home=False)
        station.vial_capper_to_ika(1)
        station.vial_ika_to_rack(1)

def rack_inspection():
    station = RobInHoodInspector("Inspection" + "_rack", sim = False, vel = 0.15)
    station.inspect_rack()
def quantos_inspection():
    station = RobInHoodInspector("Inspection" + "_quantos", sim = False, vel = 0.15)
    station.inspect_quantos()
def cartridge_inspection():
    station = RobInHoodInspector("Inspection" + "_cartridge", sim = False, vel = 0.15)
    station.inspect_filtering_cartridge()
def cartridges_rack_inspection():
    station = RobInHoodInspector("Inspection" + "_cartridges_rack", sim = False, vel = 0.15)
    station.inspect_cartridges_rack()


def execute_workflow(yaml_name):
    # Open yaml file
    station = RobInHoodInspector("Inspection" + "_rack", sim = False, vel = 0.15)
    steps = yaml
    for step in steps: 
        query = step.split('|')
        if query[0] == 'move_vial_to_pump':
            station.vial_rack_to_pump(vial_number = query[1])


if __name__ == '__main__':
    if sys.argv[1]=='inspect_rack':
        rack_inspection()
    elif sys.argv[1]=='inspect_quantos':
        quantos_inspection()
    elif sys.argv[1]=='inspect_cartridge':
        cartridge_inspection()
    elif sys.argv[1]=='inspect_cartridges_rack':
        cartridges_rack_inspection()
    elif sys.argv[1]=='demo':
        demo()
    elif sys.argv[1]=='prepare_samples':
        prepare_samples(sample_list=[0,1,2,3,4,5],capping=True)
    elif sys.argv[1] == 'stirr_samples':
        stirr_samples(hours=23,min=59,sec=59)
    elif sys.argv[1] == 'store_samples':
        #has to be in reverse order
        store_samples(vials_order=[6,5,4,3,2,1])
    elif sys.argv[1] == 'filter_samples':
        filter_samples(pouring_vial_number=int(sys.argv[2]),fresh_vial_number=int(sys.argv[3]))
    elif sys.argv[1] == 'photograph_samples':
        print(sys.argv[3])
        photograph_samples(dataset_name=sys.argv[2],path=sys.argv[3])
    elif sys.argv[1] == 'photograph_samples_pre_filter':
        photograph_samples_no_solid(dataset_name=sys.argv[2], path = sys.argv[3] + "pre_filter")
    elif sys.argv[1] == 'photograph_samples_post_nylon_filter':
        photograph_samples_no_solid(dataset_name=sys.argv[2], path = sys.argv[3] + "post_nylon_filter")
    elif sys.argv[1] == 'categorise_samples':
        categorise_samples(dataset_name=sys.argv[2])
    elif sys.argv[1] == 'move_robot':
        move_robot()
    elif sys.argv[1] == "prime_lines":
        prime_lines()
    elif sys.argv[1] == "samples_rack_to_ika":
        samples_rack_to_ika(vials_order=[1,2,3,4,5,6])
    elif sys.argv[1] == "set_down":
        set_down()
    elif sys.argv[1] == "cleaning_filtering_pump":
        cleaning_pumps()
    else:
        print("Not a valid argument.")


    
    




