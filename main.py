from drivers.rob_in_hood import RobInHood
from conf.configuration import *

def example_1(step_by_step=True):
    """
    This example is aiming to serve as a tutorial to use this script.  
    The following steps are executed:

    1. The robot picks cartridge 1 and puts it into quantos.
    2. The robot picks vial 1 and puts it into quantos.
    3. The quantos station doses 10 mg of the content in cartridge 1 into the vial.
    4. The robot moves the vial to the pump dispenser.
    5. The robot moves the vial to the IKA station.
    6. The IKA station starts stirring for 1 min 15 s.
    7. The robot takes the vial from the slot number 6 and places it into the slot number 22, which is in rack 3.
    8. The robot removes the cartridge from quantos and returns it to cartridge holder 1.
    9. The robot takes a picture of rack 3 and saves it in ...\\RobInHoodPy\\imgs\\.

    :param step_by_step: When this parameter is set to True, it is necessary to press Enter or any key to continue with the execution of the next step. 
    :type step_by_step: bool
    """
    station=RobInHood(sim=False,vel=0.05)
    station.robot.open_gripper()
    station.go_home()
    if step_by_step:
        input("[INFO] Robot ready, please press Enter to start example 1.")
    print("[INFO] Inserting cargtrige 1.") 
    # WARNING: When calling station.pick_and_place_cartridge_in_quantos(cartridge_number = 1) make sure that cartridge_number
    # is the same number as the one in station.pick_and_place_cartridge_in_holder(cartridge_number = 1). 
    # Aditionally, make sure that quantos's cartridge holeder is empty and there is a cartridge in the holder. 
    # The possible values of cartridge_number go from 1 to 3.             
    station.pick_and_place_cartridge_in_quantos(cartridge_number = 1)
    if step_by_step:
        input("[INFO] Cartridge interted press Enter to continue.")
    print("[INFO] Moving vial from rack to quantos.")
    # WARNING: When calling station.vial_rack_to_quantos(vial_number=1) make sure that the vial corresponding to vial_number
    # is in the rack. Otherwise, the robot will keep running because it cannot recognise when it did not grip a vial. 
    # the range of vial_number goes from 1 to 22.
    station.vial_rack_to_quantos(vial_number=1)
    if step_by_step:
        input("[INFO] Vial placed in quantos press Enter to continue.")
    print("[INFO] Dosing...")
    station.quantos_dosing(quantity=10)
    if step_by_step:
        input(f'[INFO] Quantos dosing task completed, press Enter to continue.')
    print("[INFO] Moving vial to pump.")
    # WARNING: Make sure that the vial holder of the pump supply is in tha right position that is twhen the needle is pointing to the left-overs vial. 
    station.vial_quantos_to_pump()
    print("[INFO] Moving vial from quantos to pump.")
    if step_by_step:
        input(f'[INFO] Vial placed in pump holder, press Enter to continue.')
    station.push_pump()
    station.pump_inyect(input_source="I3",output="I2",quantity=2000,repeat=2)
    station.pump_inyect(input_source="I3",output="I1",quantity=2000,repeat=2)
    station.pull_pump()
    if step_by_step:
        input(f'[INFO] Liquid inyection completed, press Enter to continue.')
    print("[INFO] Moving vial from pump holder to ika.")
    station.vial_pump_to_ika(ika_slot_number=6)
    if step_by_step:
        input(f'[INFO] Vial placed on ika base, press Enter to continue.')
    print("[INFO] Stirring.")
    station.ika.start_stirring()
    # WARNING: Remember to always call station.timer.set_timer(hours=0,min=1, sec=15) before station.timer.start_timer().
    station.timer.set_timer(hours=0,min=1, sec=15)
    station.timer.start_timer()
    station.ika.stop_stirring()
    if step_by_step:
        input(f'[INFO] Stirring task completed, press Enter to continue.')
    print("[INFO] Moving vial to rack")
    # WARNING: Double check that the vial_number is vailable for the robot to place the vial. The robot cannot detect which slots are free.
    # The range of ika_slot_number goes from 1 to 12 and the range of vial_number goes from 1 to 22.
    station.vial_ika_to_rack(ika_slot_number=6, vial_number=22)
    if step_by_step:
        input(f'[INFO] Vial placed, press Enter to continue.')
    print("[INFO] Returning cartrige to holder.")
    # WARNING: cartridge_number must be the same that was set in station.pick_and_place_cartridge_in_quantos(cartridge_number = 1).
    # If setting a different number, the robot may try to drop the cartridge above another cartridge. 
    station.pick_and_place_cartridge_in_holder(cartridge_number= 1) 
    if step_by_step:
        input("[INFO] Cartridge returned to holder, press Enter to continue.")
    print("[INFO] Taking pictures.")
    station.camera_to_rack(rack_number=3)
    if step_by_step:
        input("[INFO] Taking picture task completed, press enter to continue.")
    # WARNING: Call station.camera.stop_streaming() to stop the thread running the camera or artenatively open the cv window and press q.
    station.camera.stop_streaming()
    print("[INFO] Task finished.")

def example_2(step_by_step=False):
    """
    Puts vials 1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, and 20 on the IKA base.

    :param step_by_step: When this parameter is set to True, it is necessary to press Enter to continue with each step. 
    :type step_by_step: bool
    """
    station=RobInHood(sim=False,vel=0.05)
    station.robot.open_gripper()
    station.go_home()
    if step_by_step:
        input("[INFO] Robot ready... press Enter to start example 2.")
    station.vial_rack_to_ika(vial_number=1, ika_slot_number=1)

    if step_by_step:
        input("[INFO] Enter to continue.")
    station.vial_rack_to_ika(vial_number=2, ika_slot_number=2)

    if step_by_step:
        input("[INFO] Enter to continue.")
    station.vial_rack_to_ika(vial_number=3, ika_slot_number=3)

    if step_by_step:
        input("[INFO] Enter to continue.")
    station.vial_rack_to_ika(vial_number=4, ika_slot_number=4)
    
    if step_by_step:
        input("[INFO] Enter to continue.")
    station.vial_rack_to_ika(vial_number=9, ika_slot_number=5)

    if step_by_step:
        input("[INFO] Enter to continue.")
    station.vial_rack_to_ika(vial_number=10, ika_slot_number=6)

    if step_by_step:
        input("[INFO] Enter to continue.")
    station.vial_rack_to_ika(vial_number=11, ika_slot_number=7)

    if step_by_step:
        input("[INFO] Enter to continue.")
    station.vial_rack_to_ika(vial_number=12, ika_slot_number=8)

    if step_by_step:
        input("[INFO] Enter to continue.")
    station.vial_rack_to_ika(vial_number=17, ika_slot_number=9)

    if step_by_step:
        input("[INFO] Enter to continue.")
    station.vial_rack_to_ika(vial_number=18, ika_slot_number=10)

    if step_by_step:
        input("[INFO] Enter to continue.")
    station.vial_rack_to_ika(vial_number=19, ika_slot_number=11)

    if step_by_step:
        input("[INFO] Enter to continue.")
    station.vial_rack_to_ika(vial_number=20, ika_slot_number=12)

def main(step_by_step=False):
    """
    Your main function description here.

    :param step_by_step: When this parameter is set to True, it is necessary to press Enter to continue with each step. 
    :type step_by_step: bool
    """
    station = RobInHood(sim=False, vel=0.05)
    station.robot.open_gripper()
    station.go_home()
    if step_by_step:
        input("[INFO] Robot ready... press Enter to start.")
    # ...
    # Your code and comments here

if __name__ == '__main__':
    example_1(step_by_step=True)  # If not using, just comment or erase this line.
    #example_2(step_by_step=True)  # If not using, just comment or erase this line.
    #main(step_by_step=False)  # Uncomment to run your own code :)




