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

def dispense_cycle(station:RobInHood, vol: int, chemical:str):

    input_checker(station = station)

    station.infuse_position()

    station.dispense_volume(vol = vol, chemical=chemical)

    station.hold_position()

    



def make_standards_dye(station:RobInHood, dye:str):


    
    station._logger.info(f"Making Calibration standards with dye: {dye}")
    
    station.pump_prime_dispense_tubing(chemical = dye)


    station._logger.info("Making 1.5 ppm standard")

    dispense_cycle(station = station, vol = 1350, chemical=dye)


    station._logger.info("Making 1 ppm standard")

    dispense_cycle(station = station, vol = 900, chemical=dye)


    station._logger.info("Making 0.5 ppm standard")

    dispense_cycle(station = station, vol = 450, chemical=dye)


    station._logger.info("Making 0.3 ppm standard")

    dispense_cycle(station = station, vol = 270, chemical=dye)


    station._logger.info("Making 0.2 ppm standard")

    dispense_cycle(station = station, vol = 180, chemical=dye)


    station._logger.info("Making 0.1 ppm standard")

    dispense_cycle(station = station, vol = 90, chemical=dye)
    

def make_standards_water(station:RobInHood):

    

    station._logger.info("Making Calibration standards with Water(DI)")
    
    station.pump_prime_dispense_tubing(chemical = "Water(DI)")


    station._logger.info("Making 1.5 ppm standard")

    dispense_cycle(station = station, vol = 7650, chemical="Water(DI)")


    station._logger.info("Making 1 ppm standard")

    dispense_cycle(station = station, vol = 8100, chemical="Water(DI)")


    station._logger.info("Making 0.5 ppm standard")

    dispense_cycle(station = station, vol = 8550, chemical="Water(DI)")


    station._logger.info("Making 0.3 ppm standard")

    dispense_cycle(station = station, vol = 8730, chemical="Water(DI)")


    station._logger.info("Making 0.2 ppm standard")

    dispense_cycle(station = station, vol = 8820, chemical="Water(DI)")


    station._logger.info("Making 0.1 ppm standard")

    dispense_cycle(station = station, vol = 8910, chemical="Water(DI)")


def photograph_samples(station: RobInHood, dataset_name: str, samples:list):
    """
    Photographs samples and saves them in the specified path - saves them with the name of the dataset plus the liquid name
    """
    
    station._logger.info(f"Photographing samples {dataset_name} ")

  
    
    path = f"TEMP/{dataset_name}"
    try: 
        os.mkdir(path)

    except FileExistsError:
        station._logger.info(f"Directory {path} already exists")

    
    station.open_lightbox()
    
    for sample in samples:
        
        input_checker(station=station)
        
        liquid_name = sample
        solid_name = dataset_name
        station._logger.info(f"Photographing sample: {dataset_name} + {liquid_name}")
        station.close_lightbox()
        station.light_on()
        station.save_picture_from_lightbox(dye_name=liquid_name,solid_name=solid_name,path=path)
        station.light_off()
        station.open_lightbox()
       
    station.close_lightbox()
    print(path)
  



if __name__ == "__main__":

    logname="calib_standards_" + datetime.now().strftime("%d_%m_%Y_")+"_log"
    station = RobInHood(logname + "_log", sim = False, vel = 0.05)

    # station.pump.set_resolution_mode(1)
    

    # make_standards_dye(station = station, dye= "DYE1")

    # make_standards_dye(station = station, dye= "DYE2")

    # make_standards_dye(station = station, dye= "DYE3")

    # make_standards_dye(station = station, dye= "DYE4")

    # make_standards_dye(station = station, dye= "DYE5")

    # make_standards_dye(station = station, dye= "DYE6")

    # station._logger.info("Adding water to Dye 1 standards")
    # make_standards_water(station = station)

    # station._logger.info("Adding water to Dye 2 standards")
    # make_standards_water(station = station)

    # station._logger.info("Adding water to Dye 3 standards")
    # make_standards_water(station = station)

    # station._logger.info("Adding water to Dye 4 standards")
    # make_standards_water(station = station)

    # station._logger.info("Adding water to Dye 5 standards")
    # make_standards_water(station = station)

    # station._logger.info("Adding water to Dye 6 standards")
    # make_standards_water(station = station)

    samples = ["DYE1", "DYE2", "DYE3", "DYE4", "DYE5", "DYE6"]

    photograph_samples(station = station, dataset_name= "Calib_1.5_PPM", samples=samples)

    photograph_samples(station = station, dataset_name= "Calib_1_PPM", samples=samples)

    photograph_samples(station = station, dataset_name= "Calib_0.5_PPM", samples=samples)

    photograph_samples(station = station, dataset_name= "Calib_0.3_PPM", samples=samples)

    photograph_samples(station = station, dataset_name= "Calib_0.2_PPM", samples=samples)

    photograph_samples(station = station, dataset_name= "Calib_0.1_PPM", samples=samples)

    

