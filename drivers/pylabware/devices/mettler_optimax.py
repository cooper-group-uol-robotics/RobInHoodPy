"""Pylabware driver for Mettler Optimax."""

from typing import Optional, Union
from pywinauto.application import Application
import os
import psutil
import time
import logging

import serial

# Core imports
from ..controllers import LabDevice
from ..models import ConnectionParameters, LabDeviceCommands


# TODO Add error handling!

class OptimaxCommands(LabDeviceCommands):
    """Collection of commands for the Optimax
    Currently this is controlled with pywin to control the GUI since
    there is no API access for the instrument.

    This should be changed, once the API is opened, or hacked"""
    pass


class Optimax(LabDevice):
    """
    This provides a Python class for the Mettler Optimax
    based on the GUI options. For now, this is used to setup an experiment run
    and start it.
    """
    # standard_path is a class attribute (same for all instances of the class)
    standard_path = r'C:\Program Files\METTLER TOLEDO\iControl 6.1\iControl64.exe'

    def __init__(
        self,
        device_name: str,
        connection_mode: str,
        address: Optional[str],
        port: Union[str, int],
        experiment_name: str,
    ):
        # Load commands from helper class
        self.cmd = OptimaxCommands
        self.experiment_name = experiment_name
        # iControl_path is an instance attribute (can be different for each instance of the class)
        self.path = Optimax.standard_path

        # Connection settings
        connection_parameters: ConnectionParameters = {}
        connection_parameters["port"] = port
        connection_parameters["address"] = address
        connection_parameters["baudrate"] = 9600
        connection_parameters["bytesize"] = serial.SEVENBITS
        connection_parameters["parity"] = serial.PARITY_EVEN

        # Commented to avoid trying to stablish a connection
        # super().__init__(device_name, connection_mode, connection_parameters)

        # Protocol settings
        self.command_terminator = "\r\n"
        self.reply_terminator = "\r\n"
        self.args_delimiter = " "

        # This device has no command to check status
        self._heating = False
        self._stirring = False

        self.logger = logging.getLogger(
            device_name
        )

    def _find_exe_path(self):
        """Finds .exe location"""
        for root, _, files in os.walk('/'):
            for name in files:
                if name == 'iControl64.exe':
                    self.path = os.path.abspath(os.path.join(root, name))
                    self.logger.info(
                        "iControl file found, at path <%s>", self.path
                    )
                    return True
        return False

    def _test_exe_path(self):
        """Tests if iControl exe file exists at given location"""
        if os.path.isfile(self.path):
            self.logger.info(
                "iControl file found, at path <%s>", self.path
            )
            return True
        else:
            self.logger.info(
                "iControl file path not found",
            )
            return False

    def is_connected(self) -> bool:
        """Checks if app is open, and connects if it is.
        If not alrady open, perform open and connect action.
        """

        # see if path exists
        if not self._test_exe_path():
            self.logger.info(
                "iControl file path not found in standard place, trying to find the path elsewhere on computer..."
            )
            if not self._find_exe_path():
                self.logger.info(
                    "iControl file path not found anywhere on computer, failed to connect"
                )
                return False
        opened_app = 'iControl64.exe' in (i.name() for i in psutil.process_iter())
        # if iControl is not open, open and connect to it
        if not opened_app:
            # Creates app object
            self.app = Application(backend="uia").start(self.path)
            self.logger.info(
                "iControl was not open, have opened it and connected to it"
            )
            time.sleep(10)
            # TODO better way to check if open, rather than just time.sleep
            return True
        # if iControl is open, connect to it.
        self.app = Application(backend="uia").connect(path=self.path)
        self.logger.info(
            "iControl was already open, have connected to it"
        )
        # if not yet open, open it and connect
        return True

    def initialize_device(self):
        """Initilizes the app."""

        # Check if open, connect to the application
        self.is_connected()
        self.logger.info(
            "Done opening and connecting to iControl",
        )
        self.current_window = self.app.iControl

        # Creates experiment
        self._create_experiment()

    def _create_experiment(self):
        """Creates new experiment based on the operation to be executed"""
        # Click Design experiment
        self.current_window['Design Experiment'].click_input(button='left')

        # Set experiment name
        new_experiment = self.app['Design New Experiment']
        new_experiment.ExperimentNameEdit.set_text(f'{self.experiment_name}')

        # Adds experiment
        new_experiment.OKButton.click()

        # Set up new window name
        self.current_window = self.app[f'{self.experiment_name} (Design) - iControl 6.1 SP3']

    def _add_heating_step(self, temperature):
        """Adds heating step to execution"""

        self.current_window['Phase 1: Initial - Estimated start: 00:00:05'].click_input(button='left')
        # self.current_window['Phase 1: Initial - Estimated start: 00:00:05'].click_input(button='left')
        self.current_window['Heat/Cool'].click_input(button='left', double=True)

        self.current_window.EndValueEdit.set_text(f'{temperature}')
        self.current_window.OKButton.click()

    def _add_stirring_step(self, speed):
        """Adds stirring step to execution
        Speed in units of rpm
        """

        self.current_window['Phase 1: Initial - Estimated start: 00:00:05'].click_input(button='left')
        # TODO get caption name to define next window to be clicked
        self.current_window['Stir'].click_input(button='left', double=True)

        self.current_window.EndValueEdit.set_text(f'{speed} rpm')
        self.current_window.OKButton.click()

    def _add_waiting_step(self, time: int):
        """Adds waiting step to execution
        Unit of minutes
        """

        self.current_window['Phase 1: Initial - Estimated start: 00:00:05'].click_input(button='left')
        # TODO get caption name to define next window to be clicked
        self.current_window['Wait'].click_input(button='left', double=True)

        self.current_window['Wait:Edit'].set_text(f'{time} min')
        self.current_window.OKButton.click()

    def start(self):
        """Starts experiment"""

        self.current_window = self.app[f'{self.experiment_name} (Design) - iControl 6.1 SP3']
        # Start/Continue is item 7
        start_continue_item = 7

        experiment_tab = self.current_window.Experiment
        experiment_tab.click_input(button='left')
        menu_items = experiment_tab.items()
        menu_items[start_continue_item].invoke()

    def stop(self):
        """Stops experiment"""

        self.current_window = self.app[f'{self.experiment_name} (Design) - iControl 6.1 SP3']
        # Stop is item 9
        start_continue_item = 9

        experiment_tab = self.current_window.Experiment
        experiment_tab.click_input(button='left')
        menu_items = experiment_tab.items()
        menu_items[start_continue_item].invoke()

    def is_idle(self) -> bool:
        """Returns True if no stirring or heating is active."""

    def get_status(self):
        """Not supported on this device."""

    def check_errors(self):
        """Not supported on this device."""

    def clear_errors(self):
        """Not supported on this device."""

    def start_temperature_regulation(self):
        """Starts experiment."""

        self._heating = True
        self.start()

    def stop_temperature_regulation(self):
        """Stops heating."""

        self._heating = False
        self.stop()

    def start_stirring(self):
        """Starts stirring."""

        self._stirring = True
        self.start()

    def stop_stirring(self):
        """Stops stirring."""

        self._stirring = False
        self.start()

    def get_temperature(self, sensor: int = 1) -> float:
        """Gets the actual temperature.

        Args:
            sensor (int): Specify which temperature probe to read.
        """

    def get_temperature_setpoint(self, sensor: int = 0) -> float:
        """Gets desired temperature setpoint.

        Args:
            sensor (int): Specify which temperature setpoint to read.
        """
        if self._set_temperature:
            return self._set_temperature

    def get_safety_temperature(self) -> float:
        """Gets safety temperature sensor reading."""

    def get_safety_temperature_setpoint(self) -> float:
        """Gets safety temperature sensor setpoint."""

    def get_speed(self) -> int:
        """Gets current stirring speed."""

    def get_speed_setpoint(self) -> int:
        """Gets desired speed setpoint."""

    def set_speed(self, speed: int):
        """Sets the stirring speed."""

        self._add_stirring_step(speed)

    def set_temperature(self, temperature: float):
        """Sets desired temperature.

        Args:
            temperature (float): Temperature setpoint in °C.
            sensor (int): Specify which temperature probe the setpoint applies to.
        """
        self._set_temperature = temperature
        self._add_heating_step(temperature)

    def set_time(self, time: int):
        """Sets waiting time.
        This should be hanlded at a higher level once we have
        full control of the optimax

        Args:
            time (time): Time to wait in mins.
        """
        self._add_waiting_step(time)
