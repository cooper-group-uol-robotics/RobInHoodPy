import json

FILENAME='conf/json/rih_robot_motion_positions.json'
IMGS_PATH='imgs/dye_run_1/'

LOG_PATH = "/home/panda1/RobInHoodPy/RobInHoodPy/logs"
SETUP_PATH ="/home/panda1/RobInHoodPy/RobInHoodPy/robinhood/setup"
DATA_PATH = "/home/panda1/RobInHoodPy/RobInHoodPy/data"



# Becareful when restarting the computer, Linux assings a different name to every device connected after rebooting.
# To find the device name, open a terminal and type ls /dev/ttyUSB* or /dev/ttyACM* for arduino devices.
# If having issues with identifying which name belongs to each device, unplug them and connect one by one and run ls /dev/ttyUSB* or /dev/ttyACM*.
# The UBS cables have a tag with the name of the device they belong.

#When restarting, Unplug all and then plug in in the following order:
STIRRER_BARS_DISPENSER = '/dev/sb_dispenser' #'/dev/ttyACM3'
HOLDER_PORT= '/dev/holder' #'/dev/ttyACM2' ### 
LIGHTBOX_PORT='/dev/lightbox'#'/dev/ttyACM4' ### 
CAPPER_PORT='/dev/capper'#'/dev/ttyACM1' ###
FILTERINGSTATION_PORT='/dev/filt'#'/dev/ttyACM0' ### 

#When restarting, Unplug all and then plug in in the following order:
IKA_PORT = '/dev/ttyUSB0' ###
QUANTOS_PORT="/dev/ttyUSB1"
PUMP_PORT="/dev/ttyUSB2"###
ACID_PUMP_PORT = "/dev/ttyUSB3"
FILTRATIONPUMP_PORT="/dev/ttyUSB4" ###

####
SHAKER_PORT='/dev/ttyACM5000'
CAPPER_CAMERA_ID=0
LIGHTBOX_CAMERA_ID=0

VIAL_GRASP=0.0215
CAP_GRASP=0.03
QUANTOS_CARTRIDGE_GRASP=0.03
FILTERING_CARTRIDGE_GRASP=0.05

#TODO It is necessary to write a function to find the ports automaticallly.

PANDA_IP="172.16.0.2"


def read_json_cfg(filename):
    """
    This function returns 
    :param filename: Path of the file where routines of the robot are saved. 
    :return: This function returns a dictionary.
    :type string: 
    """
    cfg_raw = ''
    with open(filename) as cfg:
        cfg_raw = cfg.read()
    return json.loads(cfg_raw)


