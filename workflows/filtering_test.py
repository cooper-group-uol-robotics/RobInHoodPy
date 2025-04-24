from rob_in_hood import RobInHood
from config.configuration import *
from setup.workflow_config import PUMP_DICT, SOLIDS_DICT



SAMPLES_DICT= {

    1: {"sample_name": "Filt_1 ", "material_name": "MS 5 A", "dye_name": "Water (DI)", "vial": 1, "capping": True},
    2: {"sample_name": "Filt_2 ", "material_name": "MS 5 A", "dye_name": "Water (DI)", "vial": 2, "capping": True},
    3: {"sample_name": "Filt_2 ", "material_name": "MS 5 A", "dye_name": "Water (DI)", "vial": 3, "capping": True},
    4: {"sample_name": "Clean Vial", "material_name": None, "dye_name": "Water (DI)", "vial": 14, "capping": False},
    5: {"sample_name": "Clean Vial", "material_name": None, "dye_name": "Water (DI)", "vial": 15, "capping": False},
    6: {"sample_name": "Clean Vial", "material_name": None, "dye_name": "Water (DI)", "vial": 16, "capping": False},




}    


def preparing_filtering_station(station:RobInHood,pouring_vial_number=1,fresh_vial_number=1,cleaning_vial_number=14):
    #station=RobInHood("130924_chemspeed_capping_log", sim=False,vel=0.05)
    station.quantos.close_front_door()
    station.robot.open_gripper()
    station.pick_up_filtering_catridge()
    station.place_pouring_cleaning_vial(vial_number=cleaning_vial_number)
    station.filt_machine.filter_setup(volume_filtered=9000, wait_time=30, stepping=False)
    station.remove_pouring_vial(vial_number=cleaning_vial_number)
    station.vial_decap(pouring_vial_number)
    station.place_pouring_vial() #rename this to clarify
    station.place_filtered_vial(fresh_vial_number) #todo rename
    station.filt_machine.filter_vial(volume_filtered=9000, vacuum_time = 180, stepping=False)
    station.remove_filtered_vial(fresh_vial_number)
    station.remove_pouring_vial(pouring_vial_number)
    ###TODO ask user to replace cartridge
    station.filt_machine.clean(volume_filtered=9000,wash_solvent="system solvent", stepping=False)
    station.quantos.open_front_door()

def filter_test():
    station=RobInHood("130924_chemspeed_capping_log", sim=False,vel=0.05)
    station.filt_machine.filter_setup(volume_filtered=9000, wait_time=0)
    input("place vials")
    station.filt_machine.filter_vial(volume_filtered=9000,vacuum_time=60)
    station.filt_machine.clean(volume_filtered=9000,wash_solvent="system solvent")


def prepare_sample(station:RobInHood, file_name, sample_name, material_name, dye_name, vial,capping):
    """
    Preparation steps for dye experiment each sample gets 6 mg of specified solid and 9 ml of specified liquid.

    file_name - file_name for results file
    sample_name - sample_nane for results file
    material_name - solid material required, must match name in SOLIDS_DICT in the config file.
    dye_name - name of dye/liquid required - must match name in PUMP_DICT in the config file.
    vial - vial index
   
    
    """
    
    #station=RobInHood(sim=False,vel=0.05)

    
    liquid_port = PUMP_DICT[dye_name] #port specified in Pump_DICT
    station.hold_position()
    #exit()
    station.pump_prime_dispense_tubing(liquid_port)

    if material_name != None:
        cartridge_pos = SOLIDS_DICT[material_name] #cartridge position of material specified in material name
        if station._cartridge_in_quantos == None:
            print(f"[INFO] No cartridge loaded on quantos - placing cartridge {cartridge_pos}.")
            station.pick_and_place_cartridge_in_quantos(cartridge_pos)

        elif station._cartridge_in_quantos != cartridge_pos and station._cartridge_in_quantos != None:
            print(f"[INFO] Cartridge on quantos is from position {station._cartridge_in_quantos} - removing it.")
            station.remove_cartridge_from_quantos(station._cartridge_in_quantos)
            
            print(f"[INFO] Placing cartrige at position {cartridge_pos}")
            station.pick_and_place_cartridge_in_quantos(cartridge_pos)
        
        elif station._cartridge_in_quantos == cartridge_pos:
            print(f"[INFO] Requested cartridge at position: {station._cartridge_in_quantos} already on quantos no need to load it again.")

        else: 
            raise Exception("Unhandled cartridge loading logic")


        station.vial_rack_to_quantos(vial)
        result = station.quantos_dosing(6)
        mass = result['outcomes'][1] 
        ###removing cartridge
        station.vial_quantos_to_pump()
        
    else:
        station.vial_rack_to_pump(vial_number=vial)
        print("[INFO] No solid selected")
    
    station.infuse_position()
    station.dispense_volume(9000,liquid_port)
    station.hold_position()
    if capping:
        station.vial_pump_to_capper(to_home=False)
        station.cap()
        station.vial_capper_to_ika(vial)
        station.timer.set_timer(hours=0,min=5,sec=1)
        station.ika.start_stirring()
        station.timer.start_timer()
        station.ika.stop_stirring()
        station.vial_ika_to_rack(vial)
    else:
        station.vial_pump_to_rack(vial)
    
        



if __name__ == "__main__":
    
    file_name="Material Remover Lopez"
    sample_name="rand.sample(NAMES)"
    material_name="Adamantium Yang"
    dye_name="Coloury Smith"
    vial=1
    ###
    station=RobInHood("130924_filter_test_log", sim=False,vel=0.05)
    
    ####setup###
    #station.pump_prime_reagent_tubing(PUMP_DICT["Water (DI)"])
    #
    # station.filt_machine.prime_system_solvent(station.filt_machine.port_config["system solvent"])
    
    
    
    ####Preparing cleaning vials###### 
    #prepare_sample(station, '', SAMPLES_DICT[4]['sample_name'], SAMPLES_DICT[4]['material_name'], SAMPLES_DICT[4]['dye_name'],SAMPLES_DICT[4]['vial'],SAMPLES_DICT[4]['capping'])
    ####Preparing sample###
    #prepare_sample(station, '', SAMPLES_DICT[1]['sample_name'], SAMPLES_DICT[1]['material_name'], SAMPLES_DICT[1]['dye_name'],SAMPLES_DICT[1]['vial'],SAMPLES_DICT[1]['capping'])
    ####Filtering#########
    #preparing_filtering_station(station,pouring_vial_number=1,fresh_vial_number=7,cleaning_vial_number=14)
    #input("[INFO] Please replace the cartridge.")
    ####Preparing cleaning vials###### 
    prepare_sample(station, '', SAMPLES_DICT[5]['sample_name'], SAMPLES_DICT[5]['material_name'], SAMPLES_DICT[5]['dye_name'],SAMPLES_DICT[5]['vial'],SAMPLES_DICT[5]['capping'])
    ####Preparing sample###
    prepare_sample(station, '', SAMPLES_DICT[2]['sample_name'], SAMPLES_DICT[2]['material_name'], SAMPLES_DICT[2]['dye_name'],SAMPLES_DICT[2]['vial'],SAMPLES_DICT[2]['capping'])
    ####Filtering#########
    preparing_filtering_station(station,pouring_vial_number=2,fresh_vial_number=8,cleaning_vial_number=15)
    input("[INFO] Please replace the cartridge.")
      ####Preparing cleaning vials###### 
    prepare_sample(station, '', SAMPLES_DICT[6]['sample_name'], SAMPLES_DICT[6]['material_name'], SAMPLES_DICT[6]['dye_name'],SAMPLES_DICT[6]['vial'],SAMPLES_DICT[6]['capping'])
    ####Preparing sample###
    prepare_sample(station, '', SAMPLES_DICT[3]['sample_name'], SAMPLES_DICT[3]['material_name'], SAMPLES_DICT[3]['dye_name'],SAMPLES_DICT[3]['vial'],SAMPLES_DICT[3]['capping'])
    ####Filtering#########
    preparing_filtering_station(station,pouring_vial_number=3,fresh_vial_number=9,cleaning_vial_number=16)
    input("[INFO] Please replace the cartridge.")