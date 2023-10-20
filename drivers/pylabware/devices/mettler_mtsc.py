# external
from typing import Optional, Union, Any

import serial
import json

# Core imports
from .. import parsers as parser
from ..controllers import AbstractBalance
from ..models import ConnectionParameters, LabDeviceCommands


class MTSCCommands(LabDeviceCommands):
    """Collection of commands for the Mettler Toledo balance
    using MTSC commands"""

    # Get second external temperature setpoint
    TARE_BALANCE = {"name": "T"}
    # Turn off balance
    TURN_OFF = {"name": "PWR 0"}
    # Turn on balance
    TURN_ON = {"name": "PWR 1"}
    # Terminates running process
    STOP = {"name": "@"}
    # Write text to display
    WRITE_TXT = {"name": "D", "type": str}
    # Show weight, resets display after WRITE_TXT
    WRITE_WEIGHT = {"name": "DW"}

    # Get all commands available
    GET_COMMANDS = {"name": "I0", "reply": {"type": list, "parser": parser.slicer, "args": [-1]}}
    # Get serial numver
    GET_SERIAL_NUM = {"name": "I4", "reply": {"type": str, "parser": parser.slicer, "args": [-1]}}
    # Get target weight
    GET_TARGET_MASS = {"name": "A10", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get target weight
    GET_TARGET_MASS = {"name": "A10 0", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Gets tolerance
    GET_TOLERANCE = {"name": "A10 1", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Gets weighin mode
    GET_MODE = {"name": "C0", "reply": {"type": str, "parser": parser.slicer, "args": [-2]}}
    # Get immediate mass TODO pass units as well
    GET_STABLE_MASS = {"name": "SI", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get stable mass
    GET_STABLE_MASS = {"name": "S", "reply": {"type": float, "parser": parser.slicer, "args": [-2]}}
    # Get env condition
    GET_ENV_CONDITION = {"name": "M02", "reply": {"type": str, "parser": parser.slicer, "args": [-1]}}

    # Set how much open the door is. TODO checkl with dict
    # TODO add values to check "check": {"values": DOOR_POSITIONS}
    SET_INNER_DOOR_POS = {"name": "M40 ", "type": int}
    # TODO add values to check "check": {"values": DOOR_POSITIONS}
    # Set how much open the door is. TODO checkl with dict
    SET_DOOR_POSITION = {"name": "M37", "type": int}
    # Set number of decimals for mass TODO check dict for decimals
    # TODO add values to check "check": {"values": DOOR_POSITIONS}
    SET_MASS_READABILITY = {"name": "M23 ", "type": int}
    # TODO add values to check "check": {"values": UNITS}
    # Set weighing unit TODO dic with unit options
    SET_WEIGHTING_UNIT = {"name": "M21 0 ", "type": int}
    # Set normal weighing mode
    SET_NORMAL_MODE = {"name": "M01 0"}
    # Set sensor mode
    SET_SENSOR_MODE = {"name": "M01 2"}
    # Set target mass
    SET_TARGET_MASS = {
        "name": "A10 0",
        "type": float,
        "check": {"min": 0.0, "max": 10000.0}}


class MTSC(AbstractBalance):
    """
    Python class for the Fisher PPS4102 Balance
    """

    def __init__(
        self,
        device_name: str,
        connection_mode: str,
        port: Union[str, int],
        address: Optional[str] = None,
    ):

        # Load commands from helper class
        self.cmd = MTSCCommands

        # Connection settings
        connection_parameters: ConnectionParameters = {}
        connection_parameters["port"] = port
        connection_parameters["address"] = address
        connection_parameters["baudrate"] = 9600
        connection_parameters["bytesize"] = serial.EIGHTBITS
        connection_parameters["parity"] = serial.PARITY_EVEN
        connection_parameters["timeout"] = 3

        super().__init__(device_name, connection_mode, connection_parameters)

        # Protocol settings
        self.command_terminator = "\r\n"
        self.reply_terminator = "\r\n"
        self.args_delimiter = " "

    def prepare_message(self, cmd: dict, value: Any) -> Any:
        """Checks parameter value if necessary and prepares JSON payload"""

        message = {}
        message["endpoint"] = cmd["endpoint"]
        message["method"] = cmd["method"]

        # Prepare payload
        payload = None
        # Check that value is empty for GET requests
        if cmd["method"] == "GET":
            if value is not None:
                self.logger.warning(
                    "Trying to send GET request with non-empty payload <%s>", value
                )
        else:
            path_to_payload = cmd["path"].copy()
            parameter = path_to_payload.pop()
            payload = {parameter: value}
            # The easiest way to build the rest of the nested dict we need
            # is to start bottom up
            path_to_payload.reverse()
            # Wrap the rest of stuff around
            for item in path_to_payload:
                payload = {item: payload}
            payload = json.dumps(payload)
        message["data"] = payload
        print(message, 'llllll')
        print(payload)
        print(type(payload))
        self.logger.debug("prepare_message()::constructed payload <%s>", payload)
        return message

    def start(self):
        """"""

    def stop(self):
        """"""

    def is_idle(self):
        """Checks whether the device is in idle state."""
        return True

    def is_connected(self):
        return self.connection.is_connection_open()

    def get_status(self) -> dict:
        """Not supported in device"""

    def check_errors(self):
        """Gets errors from the device"""

    def clear_errors(self):
        """Clear errors in device"""

    def initialize_device(self):
        """Tares the balance upon initialization"""
        self.tare_balance()

    def get_mass(self) -> float:
        """Gets current mass in the balance

        Returns:
            mass(float)
        """
        return self.send(self.cmd.GET_MASS)

    def get_stable_mass(self) -> float:
        """Gets stable mass in the balance

        Returns:
            mass(float)
        """
        return self.send(self.cmd.GET_STABLE_MASS)

    def tare_balance(self):
        """Tares balance"""
        self.send(self.cmd.TARE_BALANCE)

    def turn_off(self):
        """Turns balance off"""
        self.send(self.cmd.TURN_OFF)

    def turn_on(self):
        """Turns balance on"""
        self.send(self.cmd.TURN_ON)

    def get_all_commands(self):
        """Gets all commads available in the balance"""
        self.send(self.cmd.GET_COMMANDS)
