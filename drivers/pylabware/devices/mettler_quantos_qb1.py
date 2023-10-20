"""pylabware driver for the Quantos.
"""

#TODO encapsulation on the parser function - it is a beast
#TODO TOC

from typing import Optional, Union
import serial
import re

 

# Core imports
from ..controllers import AbstractSolidDispensing
from ..exceptions import SLConnectionError, SLDeviceCommandError
from ..models import ConnectionParameters, LabDeviceCommands
from ..import parsers as parser

class QuantosQB1Commands(LabDeviceCommands):
    """Collection of commands and responses for Quantos solid dispensing."""

    #Regex for various balance/dosing unit responses
    WEIGHING_OUTCOME_REGEX = "(\d*\.\d*)|([a-zA-Z]*)"
    WEIGHING_ERROR_REGEX = "Error\s([\d]+[bt])|(I)|(\+)|(-)|(L)"
    STANDARD_ERROR_REGEX = "I\s([\d]+)|(L)|(I)"
    STANDARD_SUCCESS_REGEX = "(\d*)\s(A)|(A)"
    COMMAND_EXECUTING_REGEX = "B"
        
    # Front door positions
    FRONT_DOOR_POSITIONS = {
        "2": "Front door closed",
        "3": "Open position",
        "8": "Door not detected",
        "9": "Door running"
    }

    #Weighing result statuses
    WEIGHING_RESULT_STATUS = {

        "S": "Stable weight",
        "M": "Stable weight below minimal weight value",
        "D": "Unstable",
        "N": "Unstable below minimal weight value"
    }  

    #Statuses of the QS30 autosampler / carousel
    AUTOSAMPLER_STATUS = {
        "0": "Sampler is switched off/disabled",
        "1": "Sampler is switched on/selected"
    }

    # Error codes arrising from errors in dosing/dispensing commands
    ERROR_CODES = {
        "1": "Not mounted",
        "2": "Another job is running",
        "3": "Timeout",
        "4": "Not selected",
        "5": "Not allowed at the moment",
        "6": "Weight not stable",
        "7": "Powderflow error",
        "8": "Stopped by external action",
        "9": "Safepos error",
        "10": "Head not allowed",
        "11": "Head limit reached",
        "12": "Head expiry date reached",
        "13": "Sampler blocked.",
        "EL": "Logical Error",
        "ET": "Transmission Error",
        "ES": "Syntax Error",
        "+": "Balance Overload",
        "-": "Balance Underload",
        "I": "Unspecified internal error",
        "L": "Logical error due to incorrect parameter"
     }
    
    #List of ends of transmission for non immediatly replying commands
    NON_IMMEDIATE_END_TUPLES = (
        "A\r\n",
        "I\r\n",
        "L\r\n",
        "I 1\r\n",
        "I 2\r\n", 
        "I 3\r\n",
        "I 4\r\n",
        "I 5\r\n",
        "I 6\r\n",
        "I 7\r\n",
        "I 8\r\n",
        "I 9\r\n",
        "I 10\r\n",
        "I 11\r\n",
        "I 12\r\n",
        "I 13\r\n")

    # Error codes arising from errors in weighing commands/balance errors
    WEIGHT_RESPONSE_ERROR_CODES = {
        "1b": "Boot error - source weigh module",
        "2b": "Brand error - source weigh module",
        "3b": "Checksum error - source weigh module",
        "9b": "Option fail - source weigh module",
        "10b": "EEPROM error - source weigh module",
        "11b": "Device mismatch - source weigh module",
        "12b": "Hot plug out - source weigh module",
        "14b": "Weight module/electronic mismatch - source weigh module",
        "15b": "Adjustment needed - source weigh module",

        "1t": "Boot error - source terminal",
        "2t": "Brand error - source terminal",
        "3t": "Checksum error - source terminal",
        "9t": "Option fail - source terminal",
        "10t": "EEPROM error - source terminal",
        "11t": "Device mismatch - source terminal",
        "12t": "Hot plug out - source terminal",
        "14t": "Weight module/electronic mismatch - source terminal",
        "15t": "Adjustment needed - source terminal",

        "+": "Balance Overload",
        "-": "Balance Underload",
        "I": "Unspecified internal error",
        "L": "Logical error due to incorrect parameter"
    }

    ######weighing commands######

    # Tare
    TARE = {
        "name": "T",
        "reply": {"type": dict, "weighing": True, "immediate": False, "xml": False },
        "table": WEIGHING_RESULT_STATUS
    }

    # Get Stable Weight
    GET_STABLE_WEIGHT = {
        "name": "S",
        "reply": {"type": dict, "weighing": True, "immediate": False, "xml": False },
        "table": WEIGHING_RESULT_STATUS
    }
    ######Dosing Commands######
    # Start dosing
    START_DOSING = {
        "name": "QRA 61 1",
        "reply": {"type": dict, "weighing": False, "immediate": False, "xml": False}
    }

    # Move front door
    MOVE_FRONT_DOOR = {
        "name": "QRA 60 7",
        "type": int,
        "reply": {"type": dict, "weighing": False, "immediate": False, "xml": False}
        
    }

    MOVE_SIDE_DOOR = { 
        "name": "WS",
        "type": int,
        "reply": {"type": dict, "weighing": False, "immediate": True, "xml": False}
    
    }



    # Stop Running Dosing #This is cannot be implemented under the current construction of pylabware #FIXME
    STOP_DOSING = {
        "name": "QRA 61 4",
        "reply": {"type": dict, "weighing": False, "immediate": False, "xml": False}
        
    }

    # Get front door position
    GET_DOOR_POS = {
        "name": "QRD 2 3 7",
        "reply": {"type": dict, "weighing": False, "immediate": True, "xml": False},
        "table": FRONT_DOOR_POSITIONS
    }

    
    # Get head data
    GET_HEAD_DATA = {
        "name": "QRD 2 4 11",
        
        "reply": {
            "type": dict,
            "weighing": False, "immediate": False, "xml": True,
            "xml_tags": [
                ["Substance", "Substance"],
                ["Content Unit=\"mg\"", "Content"],
                ["Rem._dosages", "Rem._dosages"],
                ["Dosing_counter", "Dosing_counter"],
                ["Rem._quantity Unit=\"mg\"", "Rem._quantity"]]}
    }

    # Set tap before dosing - this toggles tapping on or off
    # Parameterised by tapper intensity and duration commands  
    TOGGLE_TAP_BEFORE = {"name": "QRD 1 1 1",
                      "type": int,
                      "reply":{"type": dict, "weighing": False, "immediate": True, "xml": False} }


    # Set tapper intensity for tapping before dosing in percent 
    SET_TAPPER_INTENSITY = {
        "name": "QRD 1 1 3",
        "type": int,
        "check": {"min": 10, "max": 100},
        "reply":{"type": dict, "weighing": False, "immediate": True, "xml": False}

    }

    # Set tapper duration for tapping before dosing in seconds (1-10)
    SET_TAPPER_TIME = {
        "name": "QRD 1 1 4 ",
        "type": int,
        "check": {"min": 1, "max": 10},
        "reply":{"type": dict, "weighing": False, "immediate": True, "xml": False}
    }

    # Set target value in mg
    SET_TARGET_VAUE = {
        "name": "QRD 1 1 5",
        "type": float,
        "check": {"min": 0.10, "max": 250000.00},
        "reply": {"type": dict, "weighing": False, "immediate": True, "xml": False}
    }

    # Set tolerance mode for dosing. 0 = +/- 1 = 0/+

    SET_TOLERANCE_MODE = {

        "name": "QRD 1 1 7",
        "type": int, 
        "check": {"min": 0, "max": 1},
        "reply": {"type": dict, "weighing": False, "immediate": True, "xml": False}
    }


    # Set tolerance in percentage during dosing 
    SET_TOLERANCE = {
        "name": "QRD 1 1 6",
        "type": float,
        "check": {"min": 0.1, "max": 40},
        "reply": {"type": dict, "weighing": False, "immediate": True, "xml": False}
    }

   
    # Get sample data
    GET_SAMPLE_DATA = {
        "name": "QRD 2 4 12",
       
        "reply": {
            "type": dict,
            "weighing": False, "immediate": False, "xml": True,
            "xml_tags": [
                ["Substance", "Substance"],
                ["Content Unit=\"mg\"", "Content"],
                ["Target_quantity Unit=\"mg\"", "Target_quantity"],
                ["Powder_dosing_mode", "Powder_dosing_mode"],
                ["Tapping_before_dosing", "Tapping_before_dosing"],
                ["Intensity", "Intensity"],
                ["Tolerance_Mode","Tolerance_Mode"],
                ["Tolerance Unit=\"%\"", "Tolerance"],
                ["Validity", "Validity"]]},
    }

    # Toggle head pin position
    SET_HEAD_PIN_POS = {
        "name": "QRA 60 2",
        "type": int,
        "reply": {"type": dict, "weighing": False, "immediate": False, "xml": False,}}
    

    # Set sample ID max 20 charachters
    SET_SAMPLE_ID = {
        "name": "QRD 1 1 8 ",
        "type": str,
        "check": {"min": 1, "max": 20},
        "reply": {"type": dict, "weighing": False, "immediate": False, "xml": False,}}

    # Set weighing pan as empty
    SET_VALUE_PAN = {
        "name": "QRD 1 1 9 0",
        "reply": {"type": dict, "weighing": False, "immediate": True, "xml": False}
    }

    # Set algorithm for powder dispensing 0 = standard 1 = advanced
    TOGGLE_ALGORITHM = {
        "name": "QRD 1 1 14",
        "type": int,
        "check": {"min": 0, "max": 1},
        "reply": {"type": dict, "weighing": False, "immediate": True, "xml": False}
                        }

    # Toggle antistatic
    TOGGLE_ANTISTATIC = {
        "name": "QRD 1 1 15",
        "type": int,
        "check": {"min": 0, "max": 1},
        "reply": {"type": dict, "weighing": False, "immediate": True, "xml": False}
    }


    ######Autosampler Commands######
    

    
    #Gets status of the carousel/autosampler  
    GET_SAMPLER_STATUS =  {
        "name": "QRD 2 2 8",
        "reply": {"type": dict, "weighing": False, "immediate": True, "xml": False},
        "table": AUTOSAMPLER_STATUS
    }

    # Set sampler position value between 0 (home) and 30
    SET_SAMPLER_POS = {
        "name": "QRA 60 8",
        "type": int,
        "check": {"min": 0, "max": 30},
        "reply": {"type": dict, "weighing": False, "immediate": False, "xml": False},
        
        }
    

 
class QuantosQB1(AbstractSolidDispensing):
    """
    This provides a Python class for the Mettler Quantos QB1 solid
    dispenser with QS30 Sampler. The commandas are ves on the manual:
    XXXXX TODO
    """

    def __init__(
        self,
        device_name: str,
        connection_mode: str,
        port: Union[str, int],
        address: Optional[str] = None,
    ):

        # Load commands from helper class
        self.cmd = QuantosQB1Commands

        # Connection settings
        connection_parameters: ConnectionParameters = {}
        connection_parameters["port"] = port
        connection_parameters["address"] = address
        connection_parameters["baudrate"] = 9600
        connection_parameters["bytesize"] = serial.EIGHTBITS
        connection_parameters["parity"] = serial.PARITY_NONE
        connection_parameters["timeout"] = 0 #TODO have a look at why this matters
        connection_parameters["xonxoff"] = True
        connection_parameters["receive_buffer_size"] = 128

        super().__init__(device_name, connection_mode, connection_parameters)

        # Protocol settings
        self.physical_timeout = 120
        self.command_terminator = "\r\n"
        self.reply_terminator = "\r\n"
        self.args_delimiter = " "

        #variables to keep track of balance state
        self.sampler_position = None
        self.autosampler_mounted_flag = None
        self.front_door_open = None 
        self.side_door_open = None

        #Opens the serial connection
        self.connection.open_connection()
        
        #Initialises the device - checks if autosampler is mounted and if it is homes the device
        self.initialize_device()

    
    def initialize_device(self):

       """
       Initialises the Quantos 
       1. Checks if the autosampler is mounted and if it is homes the device and sets the sampler_position variable so the 
       sample position can be tracked.
       2. If the autosampler is not mounted it will open the side doors and set the side_door_open flag.
       3. Opens the front door and sets the front_door_open flag.
       """       
      
       reply = self.get_sampler_status()
       
       
       if reply["success"] == True:
            if reply["outcomes"][0] == "Sampler is switched on/selected":
                 home_reply = self.move_sampler(0)
                 self.autosampler_mounted_flag = True

                 if home_reply["success"] == True:
                     self.sampler_position = 0
                     self.logger.info("Balance homed")

                 else: 
                     self.logger.info("Balance not homed")
    
            else: 
                self.logger.info("No carousel/autosampler connected")
                self.autosampler_mounted_flag = False
                self.sampler_position = 31 #The sampler only has 30 positions, 31 indicates no sampler. It has to be an int because of ROS.
       else:
           self.logger.warning("Error initialising the device!") 

       front_door_reply = self.open_front_door()
       
       if front_door_reply["success"] is not True:
           self.logger.warning("Error initialising the device - front door did not open!")

       if self.autosampler_mounted_flag == True:
           self.logger.info("Side doors do not open when the autosampler is mounted")
           self.side_door_open = False
            
       else:
           side_door_reply = self.open_side_door()
           
           if side_door_reply["success"] is not True:
               self.logger.warning("Side doors are not open")
             

    #Unused Commands - commands not implemented

    def start(self):
        """Device doesnt support this.
        Add a dummy function."""
        self.logger.info("Device does not support a start function")

    def stop(self):
        """Device doesnt support this.
        Add a dummy function."""
        self.logger.info("Device does not support a stop function")


    def get_status(self):
        """Not supported on this device."""
        self.logger.info("Device does not support a get status function")


    def check_errors(self):
        """Not supported on this device."""
        self.logger.info("Device does not support a check errors function")


    def clear_errors(self):
        """Not supported on this device."""
        self.logger.info("Device does not support a clear errors function")


    #Weighing Commands - commands sent to the balance
     
    def tare(self) -> dict:
        """Tares balance"""
        
        reply = self.send(self.cmd.TARE)
        
        return reply 
   
   
    def get_stable_weight(self) -> dict:
        """Gets mass in g"""


        reply = self.send(self.cmd.GET_STABLE_WEIGHT)

        return reply
   
    #Dosing Commands - commands sent to the dosing unit

       
    def start_dosing(self) -> dict:
        """Starts dosing. If successful an executing command reply 
        will be sent followed by a command executed and complete command
        once dosing is finished
        """
        
        reply = self.send(self.cmd.START_DOSING)
        
        return reply


    def stop_dosing(self):
        """Stops dosing. If successful an executing command reply will be sent
        followed by a command executed and complete command once dosing is finished
        """
    
        self.logger.info("currently not implemented")


    def open_front_door(self) -> dict:
        """Opens front door."""
        
        reply = self.send(self.cmd.MOVE_FRONT_DOOR, 3)
        
        if reply["success"] == True:
            self.front_door_open = True
        else:
            self.front_door_open = False

        return reply

     
    def close_front_door(self) -> dict:
        """Closes front door."""
        
        reply = self.send(self.cmd.MOVE_FRONT_DOOR, 2)

            
        if reply["success"] == True:
            self.front_door_open = False
        else:
            self.front_door_open = True
            
        return reply

    def open_side_door(self) -> dict:
        """ Opens the side door if autosampler not mounted"""
        
        if self.autosampler_mounted_flag == False:
            reply = self.send(self.cmd.MOVE_SIDE_DOOR, 1)
            
            if reply["success"] == True:
                self.side_door_open = True
            
            return reply
        
        else:
            self.logger.warning("Cannot open side doors if the autosampler is mounted")
            reply = {"success": False,
                     "outcomes": ["Cannot open side doors if the autosampler is mounted"]
            }
            return reply
    
    def close_side_door(self) -> dict:
        """Closes the side door if the autosampler is not mounted"""
        
        if self.autosampler_mounted_flag == False:
            reply = self.send(self.cmd.MOVE_SIDE_DOOR, 0)
            if reply["success"] == True:
                self.side_door_open = False
            
            self.side_door_open = False
            return reply
        
        else:
            self.logger.warning("Cannot close side doors if the autosampler is mounted")
            reply = {"success": False,
                     "outcomes": ["Cannot close side doors if the autosampler is mounted"]
            }
            return reply


    def get_front_door_position(self) -> dict:
        """Gets front door position"""
        reply = self.send(self.cmd.GET_DOOR_POS)

        return reply

    def get_side_door_position(self) -> dict:

        reply = {"success": True,
                 "outcomes": [self.side_door_open]}
        
        return reply

    def get_head_data(self) -> dict:
        """Gets head data."""

        reply = self.send(self.cmd.GET_HEAD_DATA)

        return reply


    def get_sample_data(self) -> dict:
        """Gets sample data from the last dispense."""

        reply = self.send(self.cmd.GET_SAMPLE_DATA)
        return reply



    def lock_dosing_head_pin(self) -> dict:
        """Move the pin down to lock the dosing head"""
       
        reply = self.send(self.cmd.SET_HEAD_PIN_POS, 4)
        return reply


    def unlock_dosing_head_pin(self) -> dict:
        """Move the pin down to unlock the dosing head"""

        reply = self.send(self.cmd.SET_HEAD_PIN_POS, 3)
        return reply

    
    def set_tapping_before_dosing(self) -> dict:
        """Sets tapping before dosing.
        """
        reply = self.send(self.cmd.TOGGLE_TAP_BEFORE, 1)
        return reply

    def unset_tapping_before_dosing(self) -> dict:
        """Un sets tapping before dosing.
        """
        reply = self.send(self.cmd.TOGGLE_TAP_BEFORE, 0)
        return reply 
    
    def set_tapper_intensity(self, intensity: int) -> dict:
        """Sets tapper intensity.

        Args:
            intensity (int): value between 10-100
        """

        reply = self.send(self.cmd.SET_TAPPER_INTENSITY, intensity)
        return reply
    
      
    def set_tapper_duration(self, duration: int) -> dict:
        """Sets tapper duration. 

        Args:
            duration (int): duration in XX for tapper. Value
            between 1-10
        """

        reply = self.send(self.cmd.SET_TAPPER_TIME, duration)
        return reply
    
    def set_target_mass(self, mass: float) -> dict:
        """Sets target mass in mg for the balance.

        Args:
            mass (float): Mass value between
            0.10 - 250000.00
        """
        reply = self.send(self.cmd.SET_TARGET_VAUE, mass)
        return reply
    
    def set_tolerance_standard(self) ->dict:
        """Sets the tolerance mode for dosing to standard (+/-)"""

        reply = self.send(self.cmd.SET_TOLERANCE_MODE, 0)
        return reply
    
    def set_tolerance_overdose(self) ->dict:
        """Sets the tolerance mode for dosing to overdose (+/0)"""
        
        reply = self.send(self.cmd.SET_TOLERANCE_MODE, 1)
        return reply


    def set_tolerance_value(self, tolerance) -> dict:
        """Sets tolerance as percentage.

        Args:
            tolerance (float): tolerance value as percentage.
            Value between 0.1-40.0
        """

        reply = self.send(self.cmd.SET_TOLERANCE, tolerance)
        return reply

   
    def set_sample_id(self, sample_id: str):
        """Sets sample ID

        Args:
            id (str): sample ID. str lenght has to be lower than 20
        """
        
        reply = self.send(self.cmd.SET_SAMPLE_ID,sample_id)
        return reply

    def set_value_pan(self) -> dict:
        """Sets pan value as empty, works like Tare."""

        reply = self.send(self.cmd.SET_VALUE_PAN)
        return reply

    def set_algorithm_standard(self):
        """Sets the algorithm to be used in dosing to standard
        """
        reply = self.send(self.cmd.TOGGLE_ALGORITHM, 0)
        return reply

    def set_algorithm_standard(self):
        """Sets the algorithm to be used in dosing to standard
        """
        reply = self.send(self.cmd.TOGGLE_ALGORITHM, 0)
        return reply

    def set_algorithm_advanced(self):
        """Sets the algorithm to be used in dosing to advanced
        """
        reply = self.send(self.cmd.TOGGLE_ALGORITHM, 1)
        return reply

    def set_antistatic_on(self) -> dict:
        """Sets antistatic on.
        """
        reply = self.send(self.cmd.TOGGLE_ANTISTATIC, 1)

        return reply

    def set_antistatic_off(self) -> dict:
        """Sets antistatic off
        """
        reply = self.send(self.cmd.TOGGLE_ANTISTATIC, 0)

        return reply


    #Autosampler Commands - commands sent to the carousel if installed
    
    def move_sampler(self, position: int):
        """
        Moves sampler.

        Args:
            position (int): Move sample to this position.
            discrete increments 0-30
            Home is 0, vials on 1-30

        """
        reply = self.send(self.cmd.SET_SAMPLER_POS, position)
        if reply["success"] == True:
            self.sampler_position = position
        
        return reply
    
    #TODO refactor
    def get_sampler_position(self) -> dict:
        """Gets sample position - the in-built command for doing this is broken. 
        Therefore it keeps track in software. """
       
        reply = {}
    
        if type(self.sampler_position) is int:
            reply["outcomes"] = self.sampler_position
            reply["success"] = True
        
        elif self.sampler_position is None:
            reply["outcomes"] = "Autosampler not initialised"
            reply["success"] = False
        
        else:
            reply["outcomes"] = "Autosampler not mounted"
            reply["success"] = False

        return reply
    
    def get_sampler_status(self) -> int:
        """Determines if the autosampler / carousel is connected or not - 
        0 autosampler is not connected
        1 autosampler is connected"""

        reply = self.send(self.cmd.GET_SAMPLER_STATUS)
        return reply

    
    def is_connected(self) -> bool:
        """Checks whether the device is connected
        by getting the door position."""

        try:
            self.send(self.cmd.GET_DOOR_POS)
            return True
        
        except SLConnectionError:
            return False

    def is_idle(self):
        """Not supported on this device"""

        self.logger.info("Device does not support an is_idle function")

    def _find_info_tags(self, reply: any, tag_list: list) -> dict:
        """Searches a return xml string for a list of tags, returns a dictionary
        with their values.

        Args:
            reply string (xml) from the balance
            tag_list: list of tags to search for

        Returns:
            reply_dict: Structured dictionary
        """

        reply_list = []

        for tag in tag_list:
            
            front_tag = f"<{tag[0]}>"
            back_tag = f"</{tag[1]}>"
            entry = re.findall(f"{front_tag}.+{back_tag}|{front_tag}{back_tag}", reply)
            
            if not entry:
                self.logger.info(f"{tag[0]}: tags not found")

            
            else:
                value = entry[0].replace(front_tag, "").replace(back_tag, "")
                list_entry = f"{tag[0]}: {value}"
                reply_list.append(list_entry)

                # TODO try, except
                if not value:
                    self.logger.info(f"{tag[0]}: tag found, but has no entry")

        return reply_list
    
    def _lookup_table(self, value: list, table : dict = False) -> list:
        
        """
        Takes a value in the form of a list of tuples and flattens that list before referencing the values in 
        the flat list against a dictionary table of stored values with meanings. If no lookup table is supplied
        searches if any of the values are A for a generic success,

        Returns: 
        A flat list of the referenced entries.
        
        """
        #flattens list of tuples 
        flattened_list = [item for sub_list in value for item in sub_list]

        #removes '' entries from the flattened list
        flattened_list = list(filter(None, flattened_list))

        output_list = []

        if not table:
            if "A" in flattened_list:
                output_list = ["Successful Execution"]
                #output_list.extend(flattened_list.remove("A"))

        else:

            for item in flattened_list:
                if item in table.keys():
                    output_list.append(table[item])

        
        if len(output_list) == 0:
            output_list = ["No Output Table Values Found"]
            output_list.extend(flattened_list)
            

        return output_list

    def _weight_response_handler(self, reply_no_name: str) -> dict:
        
        reply_dict = {
            "success" : False,
            "outcomes": [],
        }
        
        weight_match = parser.findall_parser(reply_no_name,self.cmd.WEIGHING_OUTCOME_REGEX)
        weight_match = parser.findall_stripper(weight_match)
        if weight_match:
            self.logger.info("Weighing Match")
            reply_dict["success"] = True
            result_status = self._lookup_table(weight_match, self.cmd.WEIGHING_RESULT_STATUS)
            mass = weight_match[1]
            unit = weight_match[2]
            reply_dict["outcomes"] = [result_status[0],mass,unit]
        
        weight_error_match = parser.findall_parser(reply_no_name, self.cmd.WEIGHING_ERROR_REGEX)

        if weight_error_match and not weight_match:
            self.logger.info("Weighing Error Match")
            reply_dict["success"] = False
            weight_error_cause = self._lookup_table(weight_error_match, self.cmd.WEIGHT_RESPONSE_ERROR_CODES)
            reply_dict["outcomes"] = weight_error_cause

        return reply_dict

    def _non_immediate_response_handler(self, name: str, reply_no_name: str, reply_parameters: dict, lookup_table: dict):
        
        reply_dict = {
            "success" : False,
            "outcomes": [],
                      }

        command_executing_match = parser.findall_parser(reply_no_name, self.cmd.COMMAND_EXECUTING_REGEX)

        if command_executing_match:
            self.logger.info("Command Executing Match")
            
            while not reply_no_name.endswith(self.cmd.NON_IMMEDIATE_END_TUPLES):
                
                next_reply = self.connection.receive(40) #set number of retries to large
                current_chunk = parser.stripper(next_reply.body, name)
                reply_no_name += current_chunk
               
            if reply_parameters["xml"]:
                self.logger.info("XML Match")
                reply_dict["success"] = True
                reply_dict["outcomes"] = self._find_info_tags(reply_no_name, reply_parameters["xml_tags"])
             

                if not reply_dict["outcomes"]:
                
                    command_error_match_post_execution = parser.findall_parser(reply_no_name, self.cmd.STANDARD_ERROR_REGEX)
            
                    if command_error_match_post_execution:
                    
                            self.logger.info("Command Error Match")
                            reply_dict["success"] = False
                
                            standard_error_cause = self._lookup_table(command_error_match_post_execution, self.cmd.ERROR_CODES)
                            reply_dict["outcomes"] = standard_error_cause

            else:
                
                standard_success_match = parser.findall_parser(reply_no_name, self.cmd.STANDARD_SUCCESS_REGEX)
                
                if standard_success_match:
                    self.logger.info("Standard Success Match After Executing")
                    reply_dict["success"] = True
                    standard_success_cause = self._lookup_table(standard_success_match, lookup_table)
                    reply_dict["outcomes"] = standard_success_cause
            
            return reply_dict

    def parse_reply(self, cmd: dict, reply: dict) -> dict:
        """
        Parses response from the balance and returns a
        structured dictionary response.

        Args:
            cmd: command sent
            reply: replied received
        """
        
        #uniform structure reply dictionary
        reply_dict = {
            "success" : False,
            "outcomes": ["Unhandled response", reply.body],
                      }

        #remove name from reply to allow more consistent parsing
        reply_content = reply.body

        

        reply_no_name = parser.stripper(reply_content, cmd["name"])
        
        self.logger.info(f"this is the initial reply : {reply_no_name}")
        
        #read type of response expected
        reply_parameters = cmd.get("reply")
        lookup_table = cmd.get("table")

        if reply_parameters["weighing"]:
           
           reply_dict = self._weight_response_handler(reply_no_name)

        else: 
            
            command_error_match = parser.findall_parser(reply_no_name, self.cmd.STANDARD_ERROR_REGEX)

            if command_error_match:
                self.logger.info("Command Error Match")
                reply_dict["success"] = False
                standard_error_cause = self._lookup_table(command_error_match, self.cmd.ERROR_CODES)
                reply_dict["outcomes"] = standard_error_cause


            elif not reply_parameters["immediate"]:

                reply_dict = self._non_immediate_response_handler(cmd["name"], reply_no_name, reply_parameters, lookup_table)

            elif reply_parameters["immediate"] and not command_error_match: 
                
                self.logger.info("Standard Success Match")
                standard_success_match = parser.findall_parser(reply_no_name, self.cmd.STANDARD_SUCCESS_REGEX)
                reply_dict["success"] = True
                standard_success_cause = self._lookup_table(standard_success_match, lookup_table)
                reply_dict["outcomes"] = standard_success_cause

        return reply_dict







