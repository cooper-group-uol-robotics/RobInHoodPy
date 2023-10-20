# external
from typing import Optional, Union

import serial

# Core imports
from .. import parsers as parser
from ..controllers import AbstractBalance
from ..models import ConnectionParameters, LabDeviceCommands


class PPS4102Commands(LabDeviceCommands):
    """Collection of commands for the Fisher balance PPS4102"""

    # Get mass
    GET_MASS = {
        "name": "IP",
        "reply": {
            "type": float,
            "parser": parser.researcher,
            "args": [r"[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?"],
        },
    }
    # Get stable mass
    GET_STABLE_MASS = {
        "name": "P",
        "reply": {
            "type": float,
            "parser": parser.researcher,
            "args": [r"[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?"],
        },
    }

    # Get second external temperature setpoint
    TARE_BALANCE = {"name": "T"}
    # Turn off balance
    TURN_OFF = {"name": "OFF"}
    # Turn on balance
    TURN_ON = {"name": "ON"}


class PPS4102(AbstractBalance):
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
        self.cmd = PPS4102Commands

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

    def start(self):
        """starts task"""

    def stop(self):
        """Stops task"""

    def initialize_device(self):
        """Tares the balance upon initialization"""
        self.turn_on()
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
