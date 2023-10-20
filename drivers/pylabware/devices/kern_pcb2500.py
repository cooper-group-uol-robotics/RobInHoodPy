# External
from typing import Optional, Union

import serial

# Core imports
from .. import parsers as parser
from ..controllers import AbstractBalance
from ..models import ConnectionParameters, LabDeviceCommands


class PCB2500Commands(LabDeviceCommands):
    """Collection of commands for Kern PCB balance solid dispensing."""

    # Stop dosing
    TARE_BALANCE = {"name": "t"}

    # Get mass stable or unstable
    GET_MASS = {
        "name": "w",
        "reply": {
            "type": str,
            "parser": parser.researcher,
            "args": [r"[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?"],
        },
    }
    # Get stable weighing value
    GET_STABLE_MASS = {
        "name": "s",
        "reply": {
            "type": str,
            "parser": parser.researcher,
            "args": [r"[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?"],
        },
    }


class PCB2500(AbstractBalance):
    """
    Serial Driver for Kern PCB Top Pan balance"""

    def __init__(
        self,
        device_name: str,
        connection_mode: str,
        port: Union[str, int],
        address: Optional[str] = None,
    ):

        # Load commands from helper class
        self.cmd = PCB2500Commands

        # Connection settings
        connection_parameters: ConnectionParameters = {}
        connection_parameters["port"] = port
        connection_parameters["address"] = address
        connection_parameters["baudrate"] = 9600
        connection_parameters["bytesize"] = serial.EIGHTBITS
        connection_parameters["parity"] = serial.PARITY_NONE
        connection_parameters["timeout"] = None
        connection_parameters["receive_buffer_size"] = 18

        super().__init__(device_name, connection_mode, connection_parameters)

        # Protocol settings
        self.command_terminator = "\r\n"
        self.reply_terminator = "\r\n"
        self.args_delimiter = " "

    def initialize_device(self):
        """Tares balance."""
        self.tare_balance()

    def is_connected(self) -> bool:
        """Checks whether the device is connected
        by getting the door position."""

    def is_idle(self) -> bool:
        """Returns True if no dosing is active."""

        if not self.is_connected():
            return False
        return not self._dosing

    def get_status(self):
        """Not supported on this device."""

    def check_errors(self):
        """Not supported on this device."""

    def clear_errors(self):
        """Not supported on this device."""

    def start(self):
        """Not supported on this device."""

    def stop(self):
        """Not supported on this device."""

    def get_mass(self) -> float:
        """Gets the mass

        Returns:
            mass (float)
        """
        return self.send(self.cmd.GET_MASS)

    def get_stable_mass(self) -> float:
        """Gets the mass

        Returns:
            mass (float)
        """
        return self.send(self.cmd.GET_STABLE_MASS)

    def tare_balance(self):
        """Tares the balance"""
        self.send(self.cmd.TARE_BALANCE)
