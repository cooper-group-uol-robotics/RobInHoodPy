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
    station = RobInHood(sim=False, vel=0.05)
    station.robot.open_gripper()
    station.go_home()
    if step_by_step:
        input("[INFO] Robot ready, please press Enter to start example 1.")
    print("[INFO] Inserting cartridge 1.")
    # ...
    # Your code and comments here

def example_2(step_by_step=False):
    """
    Puts vials 1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, and 20 on the IKA base.

    :param step_by_step: When this parameter is set to True, it is necessary to press Enter to continue with each step. 
    :type step_by_step: bool
    """
    station = RobInHood(sim=False, vel=0.05)
    station.robot.open_gripper()
    station.go_home()
    if step_by_step:
        input("[INFO] Robot ready... press Enter to start example 2.")
    station.vial_rack_to_ika(vial_number=1, ika_slot_number=1)
    # ...
    # Your code and comments here

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
    main(step_by_step=False)  # Uncomment to run your own code :)




