from rob_in_hood import RobInHood
from config.configuration import *
import math
import time

vials={1:['water','3'],
           2:['water','3'],
           3: ['water', '3'],
           4: ['water', '3'],
           
           5: ['ethanol', '4'],
           6: ['ethanol', '4'],
           7: ['ethanol', '4'],
           8: ['ethanol', '4'],
           
           9: ['acetone', '5'],
           10: ['acetone', '5'],
           11: ['acetone', '5'],
           12: ['acetone', '5']
           
           }
def control_experiment(step_by_step=False):
    station=RobInHood(sim=False,vel=0.05)
    station.robot.open_gripper()
    station.hold_position()
    for t in range(0,40):
        for i in [1,2,3,4,5,6,7,8,9,10,11,12]:    
            station.vial_rack_to_pump(i)
            station.shut_door()
            station.quantos.tare()
            station.quantos.open_front_door()
            station.quantos.open_side_door()
            station.vial_pump_to_quantos()
            station.shut_door()
            station.log_weight(vials[i][0],str(i), str(station.take_weight()))
            station.log_weight(vials[i][0],str(i), str(station.take_weight()))
            station.log_weight(vials[i][0],str(i), str(station.take_weight()))
            station.quantos.open_front_door()
            station.quantos.open_side_door()
            station.vial_quantos_to_rack(i)
        #station.timer.set_timer(hours=1,min=0,sec=0)
        #station.timer.start_timer()
    station.go_home()

def main(step_by_step=False):
    station=RobInHood(sim=False,vel=0.05)
    station.robot.open_gripper()
    #station.hold_position()
    ##station.initialise_pump()
    # station.pump_prime_dispense_tubing(3)
    # for i in [1,2,3,4]:
    #     station.vial_rack_to_pump(i)
    #     ##fill
    #     station.dispense_vol(10000, vials[i][1])
    #     ###
    #     station.vial_pump_to_capper()
    #     station.cap()
    #     station.vial_capper_to_pump()
    #     station.quantos.close_front_door()
    #     station.quantos.close_side_door()
    #     station.quantos.tare()
    #     station.quantos.open_front_door()
    #     station.quantos.open_side_door()
    #     station.vial_pump_to_quantos()
    #     station.shut_door()
    #     station.log_weight(vials[i][0],str(i), str(station.take_weight()))
    #     station.log_weight(vials[i][0],str(i), str(station.take_weight()))
    #     station.log_weight(vials[i][0],str(i), str(station.take_weight()))
    #     station.quantos.open_front_door()
    #     station.quantos.open_side_door()
    #     station.vial_quantos_to_rack(i)
    # station.pump_prime_dispense_tubing(4)
    # for i in [5,6,7,8]:
    #     station.vial_rack_to_pump(i)
    #     ##fill
    #     station.dispense_vol(10000, vials[i][1])
    #     ###
    #     station.vial_pump_to_capper()
    #     station.cap()
    #     station.vial_capper_to_pump()
    #     station.quantos.close_front_door()
    #     station.quantos.close_side_door()
    #     station.quantos.tare()
    #     station.quantos.open_front_door()
    #     station.quantos.open_side_door()
    #     station.vial_pump_to_quantos()
    #     station.shut_door()
    #     station.log_weight(vials[i][0],str(i), str(station.take_weight()))
    #     station.log_weight(vials[i][0],str(i), str(station.take_weight()))
    #     station.log_weight(vials[i][0],str(i), str(station.take_weight()))
    #     station.quantos.open_front_door()
    #     station.quantos.open_side_door()
    #     station.vial_quantos_to_rack(i)
    # station.pump_prime_dispense_tubing(5)
    # for i in [9,10,11,12]:
    #     station.vial_rack_to_pump(i)
    #     ##fill
    #     station.dispense_vol(10000, vials[i][1])
    #     ###
    #     station.vial_pump_to_capper()
    #     station.cap()
    #     station.vial_capper_to_pump()
    #     station.quantos.close_front_door()
    #     station.quantos.close_side_door()
    #     station.quantos.tare()
    #     station.quantos.open_front_door()
    #     station.quantos.open_side_door()
    #     station.vial_pump_to_quantos()
    #     station.shut_door()
    #     station.log_weight(vials[i][0],str(i), str(station.take_weight()))
    #     station.log_weight(vials[i][0],str(i), str(station.take_weight()))
    #     station.log_weight(vials[i][0],str(i), str(station.take_weight()))
    #     station.quantos.open_front_door()
    #     station.quantos.open_side_door()
    #     station.vial_quantos_to_rack(i)
    # for i in [13,14,15,16]:
    #     station.vial_rack_to_pump(i)
    #     station.vial_pump_to_capper()
    #     station.cap()
    #     station.vial_capper_to_pump()
    #     station.quantos.close_front_door()
    #     station.quantos.close_side_door()
    #     station.quantos.tare()
    #     station.quantos.open_front_door()
    #     station.quantos.open_side_door()
    #     station.vial_pump_to_quantos()
    #     station.shut_door()
    #     station.log_weight(vials[i][0],str(i), str(station.take_weight()))
    #     station.log_weight(vials[i][0],str(i), str(station.take_weight()))
    #     station.log_weight(vials[i][0],str(i), str(station.take_weight()))
    #     station.quantos.open_front_door()
    #     station.quantos.open_side_door()
    #     station.vial_quantos_to_rack(i)
    for t in range(0,40):
        for i in [1,2,3,4,5,6,7,8,9,10,11,12]:    
            station.vial_rack_to_pump(i)
            station.shut_door()
            station.quantos.tare()
            station.quantos.open_front_door()
            station.quantos.open_side_door()
            station.vial_pump_to_quantos()
            station.shut_door()
            station.log_weight(vials[i][0],str(i), str(station.take_weight()))
            station.log_weight(vials[i][0],str(i), str(station.take_weight()))
            station.log_weight(vials[i][0],str(i), str(station.take_weight()))
            station.quantos.open_front_door()
            station.quantos.open_side_door()
            station.vial_quantos_to_rack(i)
        station.timer.set_timer(hours=1,min=0,sec=0)
        station.timer.start_timer()
    station.go_home()
        #pause 1 hour
    #station.vial_quantos_to_pump()
    #station.hold_position()
    #station.infuse_position()
    
    #station.vial_pump_to_capper()
    #station.cap()
    #station.vial_capper_to_ika()
    #station.shaker_on()
    #time.sleep(10)-0.076682, 0.146687, -0.054647]

    #station.shaker_off()
    #station.go_home()
    #if step_by_step:
    #    input("[INFO] Robot ready... press Enter to start.")
    ### YOUR CODE GOES HERE ###

    ###########################

def move_from_current():
    station=RobInHood(sim=False,vel=0.1)
    station.linear_test([-0.020624, 0.343206, 0.154030, math.pi/2, 0.0, 0.0])

def cartridge_test():
    station=RobInHood(sim=False,vel=0.1)
    station.go_home()
    station.pick_and_place_cartridge_in_quantos(1)
    station.remove_cartridge_from_quantos(1)
    station.go_home()
def ika_test():
    station=RobInHood(sim=False,vel=0.1)
    station.robot.open_gripper()
    station.go_home()
    for i in range(1,11):
        station.vial_rack_to_pump(i)
        station.vial_pump_to_capper()
        station.vial_capper_to_ika(i)
        station.go_home()
def ika_to_rack_test():
    station=RobInHood(sim=False,vel=0.1)
    station.robot.open_gripper()
    station.go_home()
    for i in [10,9,8,7,6,5,4,3,2,1]:
        station.take_weight()
        #station.vial_pinfusing_position(sump_to_rack(i)
        station.vial_ika_to_rack(i)
def capper_test():
    station=RobInHood(sim=False,vel=0.1)
    station.go_home()
    station.camera.stop_streaming()
    station.cap()

def rest_of_racks():
    station=RobInHood(sim=False,vel=0.1)
    station.robot.open_gripper()
    station.go_home()
    station.vial_rack_to_pump(13)
    station.vial_pump_to_rack(13)
def decapper_test():
    station=RobInHood(sim=False,vel=0.1)
    station.robot.open_gripper()
    station.go_home()
    station.remove_cap()

def dispense_move(pos):
    station=RobInHood(sim=False,vel=0.1)
    
    if pos == 0:
        station.hold_position()
    
    if pos == 1:
        station.infuse_position()

def Quantos_test():
    station=RobInHood(sim=False,vel=0.1)

   
  

    x = station.quantos_dosing(10)

    print(x)

    log_info("test_name", x["outcomes"][1], 9 )
 

    #print(weight)
    #station.log_weight("test", "test_log", str(weight))
    
    
    # x = station.quantos.zero()

    #print(x)
def pump_test():
    station=RobInHood(sim=False,vel=0.1)
    #station.initialise_pump()
    #station.pump.check_errors()
    #station.infuse_position()
    #station.hold_position()
    station.pump.clear_errors()
    station.pump_prime_reagent_tubing(5)
    station.pump_prime_reagent_tubing(7)
    station.pump_prime_reagent_tubing(8)
    station.pump_prime_dispense_tubing(9)
    station.pump_prime_dispense_tubing(11)
    station.pump_prime_dispense_tubing(11)
    #station.pump_prime_dispense_tubing(12)
    
    #station.infuse_position()
    #station.pump_prime_reagent_tubing(8)
    #station.infuse_position()
    

def contamination_test_setup():
    """Sets up the dispense line for a contamination test"""
    station = RobInHood(sim=False, vel = 0.1)

    print("[INFO] dispensing 4000 ml MO into 40 ml waste vial")
    station.hold_position()
    station.pump.dispense(volume = 4000, source_valve = 7, destination_valve= 1)
    
    print("[INFO] dispensing 5 ml MO 10 PPM into a vial" )
    station.infuse_position()
    station.pump.dispense(volume = 5000, source_valve= 7, destination_valve = 1)

    station.hold_position()
    print("[INFO] moving 2 ml MO 10 PPM from dispense to waste bottle 6")
    station.pump.dispense(volume = 2000, source_valve= 1, destination_valve=6)
    
    

def forward_priming_test(wash_amount):
    """Test of forward priming procedure""" 
    station = RobInHood(sim=False, vel = 0.1)
    
    print(f"[INFO] forward priming {wash_amount} into 40ml waste vial")
    station.hold_position()
    station.pump.dispense(volume = wash_amount, source_valve=8, destination_valve=1)
    
    print("Dispensing 5 ml sample into a vial")
    station.infuse_position()
    station.pump.dispense(volume = 5000, source_valve =8, destination_valve=1)

    print("Returning vial")
    station.hold_position()

def backwards_priming_test(repeats):
    """Test of backwards priming procedure"""
    station = RobInHood(sim= False, vel =0.1)
    
    cycle = 0 


    while cycle < repeats:
        print(f"This is the {cycle+1} backward priming cycle")        
        print("Pushing 1 ml water - overspill into the waste vial")
        station.hold_position()
        station.pump.dispense(volume = 1000, source_valve=8, destination_valve=1)

        print("Pulling 2 ml volume from dispense line to waste bottle 6")
        station.pump.dispense(volume =2000, source_valve=1, destination_valve=6)
        
        cycle = cycle + 1

    print("priming the dispense line")
    station.pump.dispense(volume = 1000, source_valve=8, destination_valve= 1)
    
    print("Dispensing 5 ml sample into a vial")
    station.infuse_position()
    station.pump.dispense(volume = 5000, source_valve =8, destination_valve=1)

    print("Returning vial")
    station.hold_position()


def log_info(sample_name, material_weight, dye_volume):
    file_name = 'test'
    f = open("log/"+file_name+".txt", "a+")
    time_obj = time.localtime()
    f.write(f'{sample_name}:\t {material_weight}:\t {dye_volume}:\t {time.asctime(time_obj)}:\n')
    f.close()

if __name__ == '__main__':
    pump_test()




