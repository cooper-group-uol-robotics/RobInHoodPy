from rob_in_hood import RobInHood
from conf.configuration import *
from conf.workflow_config_yushu_dye import PUMP_DICT, SOLIDS_DICT
import math
import time
import logging
import os




SAMPLES_DICT= {

    1: {"sample_name": "5_3", "material_name": "MS Y", "dye_name": "DYE_3", "vial": 1},
    2: {"sample_name": "5_4", "material_name": "MS Y", "dye_name": "DYE_4", "vial": 2},
    3: {"sample_name": "5_5", "material_name": "MS Y", "dye_name": "DYE_5", "vial": 3},
    4: {"sample_name": "5_6", "material_name": "MS Y", "dye_name": "DYE_6", "vial": 4},
    5: {"sample_name": "6_1", "material_name": "MS 13X", "dye_name": "DYE_1", "vial": 5},
    6: {"sample_name": "6_2", "material_name": "MS 13X", "dye_name": "DYE_2", "vial": 6},
    7: {"sample_name": "6_3", "material_name": "MS 13X", "dye_name": "DYE_3", "vial": 7},
    8: {"sample_name": "6_4", "material_name": "MS 13X", "dye_name": "DYE_4", "vial": 8},
    9: {"sample_name": "6_5", "material_name": "MS 13X", "dye_name": "DYE_5", "vial": 9},
    10: {"sample_name": "6_6", "material_name": "MS 13X", "dye_name": "DYE_6", "vial": 10},
    

}







def prepare_sample(station, file_name, sample_name, material_name, dye_name, vial):
    """
    Preparation steps for dye experiment each sample gets 6 mg of specified solid and 9 ml of specified liquid.

    file_name - file_name for results file
    sample_name - sample_bane for results file
    material_name - solid material required, must match name in SOLIDS_DICT in the config file.
    dye_name - name of dye/liquid required - must match name in PUMP_DICT in the config file.
    vial - vial index
   
    
    """
    
    #station=RobInHood(sim=False,vel=0.05)

    cartridge_pos = SOLIDS_DICT[material_name] #cartridge position of material specified in material name
    liquid_port = PUMP_DICT[dye_name] #port specified in Pump_DICT
    station.hold_position()
    station.pump_prime_dispense_tubing(liquid_port)

    if station._cartridge_in_quantos == None:
        print(f"[INFO] No cartridge loaded on quantos - placing cartridge {cartridge_pos}")
        station.pick_and_place_cartridge_in_quantos(cartridge_pos)

    elif station._cartridge_in_quantos != cartridge_pos and station._cartridge_in_quantos != None:
        print(f"[INFO] Cartridge on quantos is from position {station._cartridge_in_quantos} - removing it")
        station.remove_cartridge_from_quantos(station._cartridge_in_quantos)
        
        print(f"[INFO] Placing cartrige at position {cartridge_pos}")
        station.pick_and_place_cartridge_in_quantos(cartridge_pos)
    
    elif station._cartridge_in_quantos == cartridge_pos:
        print(f"[INFO] Requested cartridge at position: {station._cartridge_in_quantos} already on quantos no need to load it again")

    else: 
        raise Exception("Unhandled cartridge loading logic")
        
    
    station.vial_rack_to_quantos(vial)
    result = station.quantos_dosing(6)
    mass = result['outcomes'][1] 
    station.vial_quantos_to_pump()
    station.infuse_position()
    station.dispense_volume(9000,liquid_port)
    station.hold_position()
    station.vial_pump_to_capper()
    station.cap()
    station.vial_capper_to_ika(vial)
    #station.remove_cartridge_from_quantos(cartridge_pos)
    results_info(file_name = file_name, sample_name = sample_name,material_ID = material_name, material_weight= mass,dye_ID= dye_name, dye_vol= 9)


def results_info(file_name, sample_name, material_ID, material_weight, dye_ID,dye_vol):
    f = open("log/"+file_name+".txt", "a+")
    time_obj = time.localtime()
    #f.write(f'sample_name:\tmaterial (type):\tmaterial weight (g):\tdye (type):\tdye volume (uL)\tTime \n')
    f.write(f'{sample_name}\t{material_ID}\t{material_weight}\t{dye_ID}\t{dye_vol}\t{time.asctime(time_obj)}:\n')
    f.close()

def stir_samples(station):
    #station=RobInHood(sim=False,vel=0.05)
  

    station.ika.set_speed(500)
    station.ika.start_stirring()
    station.timer.set_timer(hours = 0, min = 0, sec = 20) #TODO FIX!!!!
    station.timer.start_timer()

    station.ika.stop_stirring()
def take_photos(station):

    #station=RobInHood(sim=False,vel=0.05)
  
    station.dataset_generation([],[1,2,3,4,5,6,7,8,9,20],"yushu_test_after_filtration")

def check_experiment_setup(sample_dict, file_name):
    for entry in sample_dict:
 
      
        material_name = sample_dict[entry]["material_name"]
        dye_name = sample_dict[entry]["dye_name"]

       
        
        
        
        if material_name in SOLIDS_DICT.keys() and dye_name in PUMP_DICT.keys():
        

            print(f"[INFO] Solid material: {material_name} at cartridge position: {SOLIDS_DICT[material_name]}")

            print(f"[INFO] Dye: {dye_name} at valve port: {PUMP_DICT[dye_name]}")

        else:
            raise KeyError("Material or Dye not in dictionary")
    
   
    if os.path.isfile("log/"+file_name+".txt"):
        print("[WARNING] results file exists - exiting")
        exit()

    f = open("log/"+file_name+".txt", "a+")
    print("#Input dictionary of Samples that were run:")
    
    for entry in sample_dict:
        f.write(f"#{sample_dict[entry]}\n")



    f.write(f'#sample_name:\tmaterial (type):\tmaterial weight (g):\tdye (type):\tdye volume (mL)\tTime \n')
    f.close()


if __name__ == "__main__":
    
    station = RobInHood("02052024_wash_log",  sim=False,vel=0.05)
  
    
    file_name = ""
  
    check_experiment_setup(SAMPLES_DICT,file_name)


    for entry in SAMPLES_DICT.keys():
  
        prepare_sample(station, file_name, SAMPLES_DICT[entry]["sample_name"], SAMPLES_DICT[entry]["material_name"], SAMPLES_DICT[entry]["dye_name"], 
                       SAMPLES_DICT[entry]["vial"])
    
    

    print(f"[INFO] Unloading last cartridge back to position: {station._cartridge_in_quantos}")
    station.remove_cartridge_from_quantos(station._cartridge_in_quantos)

    stir_samples(station)
    for i in [10,9,8,7,6,5,4,3,2,1]:
       station.vial_ika_to_rack(i)
    
    station.pump_prime_dispense_tubing(3)

    print("[INFO] Success!! :D")
    
