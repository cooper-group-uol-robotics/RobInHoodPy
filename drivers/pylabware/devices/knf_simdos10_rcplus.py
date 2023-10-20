from typing import Any, Dict, Union, Optional
import serial

# Core import
from .. import parsers as parser
from ..controllers import (
    AbstractDispensingController,
    in_simulation_device_returns,
)
from ..exceptions import (
    SLConnectionError,
    SLDeviceInternalError,
    SLDeviceCommandError
)
from ..models import ConnectionParameters, LabDeviceCommands


class RCPlusCommands(LabDeviceCommands):
    """Collection of command definitions for SimDOS RC Plus diaphragm pump."""

    MODES = {
        '0': 'Run mode active',
        '1': 'Dispense mode mL and time active',
        '2': 'Dispense mode mL/min and time active'
    }
    CYCLES = {
        '0': 'Function off',
        '1': 'Deactivated',
        '1000': 'Infinite'
    }
    ANALOG_SIGNAL_TYPES = {
        '0': '0....10V',  # Default
        '1': '0....20 mA',
        '2': '4....20 mA',
        '3': '0....5 V',
        '9': 'OFF',
    }
    ANALOG_SPEEDS = {
        '0': '1-100 range',  # Default
        '1': '0.3-30 range',
        '2': '0.15-15 range',
    }
    DIGITAL_FUNCTIONS = {
        '00': 'Signal off',  # Default
        '01': 'level controlled',
        '06': 'edge controlled',
    }
    PROFILES = {
        '0': 'Standard',  # Default
        '1': 'Volatile',
        '2': 'Viscous',
        '3': 'Highly viscous',
        '4': 'Reserved'
    }
    OPERATION_STATUS = {
        1 :  {"0" : "Motor turns",
              "1" : "Pump fault",
              "2" : "Display OFF"},
        2 : {"0" : "Motor adjusted",
             "1" : "I/O 1 input high",
             "2" : "I/O 2 input high",
             "3" : "Motor on UT"},
        3 : {"0" : "Run mode started"},
        4 : {"0" : "Dispense-mode started",
             "3" : "User stop NOT active"},
        6 : {"0" : "Overpressure",
             "1" : "Reserved",
             "2" : "Reserved",
             "3" : "Analog signal under 4mA",
             "4" : "Power supply failure",
             "5" : "Motor error",
             "6" : "Temperature exceeded",
             "7" : "No encoder sensor signal"}
    }
    # ################### Read commands ###################################
    # Read mode
    GET_MODE = {"name": "?MS", "reply": {"type": str}}
    # Get speed
    GET_SPEED = {
        "name": "?RV",
        "reply": {
            "type": str,
            "parser": parser.left_strip,
            "args": ["0"]}}
    # Get set dispense volume for dispense mode
    GET_DISPENSE_VOL = {
        "name": "?DV",
        "reply": {
            "type": str,
            "parser": parser.left_strip,
            "args": ["0"]}}
    # Get time for dispense mode
    GET_TIME = {"name": "?DT", "reply": {"type": str}}
    # Get cycles
    GET_CYCLES = {
        "name": "?DN",
        "reply": {
            "type": str,
            "parser": parser.left_strip,
            "args": ["0"]}}
    # Break time in between cycles
    GET_BREAK_TIME = {
        "name": "?DB",
        "reply": {
            "type": str,
            "parser": parser.left_strip,
            "args": ["0"]}}
    # Get time counter
    GET_TIME_COUNTER = {
        "name": "?TT",
        "reply": {"type": str}}
    # Get dispense volume counter in µl
    GET_VOL_COUNTER = {
        "name": "?TV",
        "reply": {
            "type": str,
            "parser": parser.left_strip,
            "args": ["0"]}}
    # Get firmware version
    GET_FIRMWARE = {
        "name": "?SV",
        "reply": {
            "type": str,
            "parser": parser.slicer,
            "args": [5, 10]}}
    # Get model
    GET_MODEL = {
        "name": "?SV",
        "reply": {
            "type": str,
            "parser": parser.slicer,
            "args": [0, 5]}}
    # Get status
    GET_STATUS = {"name": "?SS", "reply": {"type": str}}
    # Get profile
    GET_PROFILE = {"name": "?CC", "reply": {"type": str}}
    # Get calibration factor
    GET_CALIBRATION_FACTOR = {"name": "?CH", "reply": {"type": str}}
    # Get pump address
    GET_ADDRESS = {"name": "?AD", "reply": {"type": str}}

    # ################### Control commands ###################################
    # Stop
    STOP = {"name": "KY0", "reply": {"type": str, "set": True}}
    # Start
    START = {"name": "KY1", "reply": {"type": str, "set": True}}
    # Prime
    PRIME = {"name": "KY2", "reply": {"type": str, "set": True}}
    # Pause
    PAUSE = {"name": "KY3", "reply": {"type": str, "set": True}}
    # Initialize valve only
    INIT_PUMP = {"name": "IN", "reply": {"type": str, "set": True}}
    # Reset pump to factory settings
    RESET = {"name": "IP", "reply": {"type": str, "set": True}}
    # Check communication, Returns pump address if communication works correctly
    COM_CHECK = {"name": "?SI", "reply": {"type": str}}

    # Select run mode of the pump
    SET_RUN_MODE = {"name": "MS0", "reply": {"type": str, "set": True}}
    # Dispense mode ml and time is active
    SET_DISPENSE_MODE = {"name": "MS1", "reply": {"type": str, "set": True}}
    # Dispense mode ml/min and time is active
    SET_DISPENSE_MODE_ML_MIN = {"name": "MS2", "reply": {"type": str, "set": True}}
    # Sets flow rate in µl/min
    SET_SPEED = {
        "name": "RV",
        "type": int,
        "check": {"min": 1000, "max": 100000},
        "rjust": 8,
        "reply": {"type": str, "set": True}
    }
    # Sets the dispense volume in dispense mode, in µl
    SET_DISPENSE_VOL = {
        "name": "DV",
        "type": int,
        "check": {"min": 1000, "max": 999999},
        "rjust": 8,
        "reply": {"type": str, "set": True}
    }
    # Set time in dispense mode
    SET_TIME = {
        "name": "DT",
        "type": int,
        "check": {"min": 100, "max": 99595999},
        "rjust": 8,
        "reply": {"type": str, "set": True}
    }
    # Set pump address
    SET_ADDRESS = {"name": "AD", "reply": {"type": str, "set": True}}
    # Set number of cycles
    SET_CYCLES = {
        "name": "DN",
        "type": int,
        "check": {"min": 2, "max": 1000},
        "rjust": 5,
        "reply": {"type": str, "set": True}
    }
    # Set number of cycles
    SET_BREAK_TIME = {
        "name": "DB",
        "type": int,
        "check": {"min": 1, "max": 5999},
        "rjust": 5,
        "reply": {"type": str, "set": True}
    }
    # TODO - check error handing when invalid profile value entered
    # Set liquid profile
    SET_PROFILE = {
        "name": "CC",
        "type": str,
        "check": {"values": PROFILES},
        "reply": {"type": str, "set": True}
    }
    # Set calibration factor
    SET_CALIBRATION_FACTOR = {
        "name": "CH",
        "type": int,
        "check": {"min": 8000, "max": 12000},
        "rjust": 5,
        "reply": {"type": str, "set": True}
    }


class RCPlus(AbstractDispensingController):
    """
    This provides a Python class for the KNF SIMDOS 10 RC Plus diaphragm pump
    based on the the original operation manual CP_SIMDOS02_EN_04_166851.docx
    """

    def __init__(
        self,
        device_name: str,
        connection_mode: str,
        port: Union[str, int],
        switch_address: str,
        address: Optional[str] = None,
    ):
        # Load commands from helper class
        self.cmd = RCPlusCommands

        # TODO Check pump address is between 00-99
        self._switch_address = switch_address

        # Connection settings
        connection_parameters: ConnectionParameters = {}
        # TCP/IP relevant settings
        connection_parameters["port"] = port
        connection_parameters["address"] = address
        # RS-232/RS-485 relevant settingsx
        connection_parameters["baudrate"] = 9600
        connection_parameters["bytesize"] = serial.EIGHTBITS
        connection_parameters["parity"] = serial.PARITY_NONE
        connection_parameters["receive_timeout"] = 0.1

        super().__init__(device_name, connection_mode, connection_parameters)

        # Protocol settings
        self.command_prefix = '\x02'
        self.command_terminator = '\x03'
        self.reply_prefix = '\x02'
        self.reply_terminator = '\x03'
        self.args_delimiter = ""
        self.reply_ACK = "\x06"  # command acknowleged
        self.reply_NACK = "\x21"  # command not acknowledged
        # Pump status byte
        self._last_status = 0

    def _check_mode(self):
        """Checks mode"""
        if self.get_mode() != 'Run mode active':
            self.logger.debug(
                "Pump not in correct mode for this command - needs to be in run mode"
            )
            raise SLDeviceCommandError

    def compute_checksum(self, command_str: str):
        # TODO make this do a proper checksum calculation
        # for now, just returning "U" to mean use no checksum.
        """Computes the checksum of the command"""

        return "U"

    def prepare_message(self, cmd: Dict, value: Any) -> str:
        """This function does all preparations needed to make the command
        compliant with device protocol, e.g. type casts the parameters, checks
        that their values are in range, adds termination sequences, etc.

        This method is redefined in this child class from the super class.

        Args:
            cmd: Device command definition.
            value: Command parameter to set, if any.

        Returns:
            (str): Checked & prepared command string.
        """

        if value is None:
            command_str = (
                self.command_prefix
                + self._switch_address
                + cmd["name"]
                + self.command_terminator
            )
        else:
            command_str = (
                self.command_prefix
                + self._switch_address
                + cmd["name"]
                + self.args_delimiter
                + str(value)
                + self.command_terminator
            )

        # Apply checksum
        checksum = self.compute_checksum(command_str)

        # Create and return the final message with the checksum on the end
        return command_str + checksum

    def _recv(self, cmd: Dict) -> Union[int, float, str, bool]:
        """Locks the connection object, reads back the reply and re-assembles it
        if it is chunked. Then parses the reply if necessary and passes it back.

        This method normally shouldn't be redefined in child classes.
        But we are redefining it here due to the need to remove the checksum at the end.
        FIXME

        Args:
            parse: If reply parsing is required.

        Returns:
            (str): Reply from the device.
        """

        if self.simulation is True:
            self.logger.info("SIM :: Received reply.")
            return ""
        with self._lock:
            reply = self.connection.receive()
            # if it was a setter command, we will receive back only ACK/NACK
            # and then no further processing is needed
            setter = cmd["reply"].get("set", False)
            if setter:
                reply = self.check_errors(reply)
                return reply

            # Removes the checksum from the end
            reply.body = reply.body[:-1]
            # Check if we got complete reply in case it is chunked
            # If not, keep reading out data until the terminator
            # TODO how (any) parameters should be appended to reply object?
            if reply.content_type == "chunked":
                if self.reply_terminator is not None or self.reply_terminator != "":
                    while not reply.body.endswith(self.reply_terminator):
                        self.logger.debug(
                            "_recv()::reply terminator not found, reading next chunk."
                        )
                        reply_chunk = self.connection.receive()
                        reply.body = reply.body + reply_chunk.body

                else:
                    self.logger.warning(
                        "Received chunked reply, but reply terminator is not set - reassembly not possible!"
                    )
        self.logger.debug("Raw reply from the device: <%r>", reply.body)

        # Usually, we don't expect empty replies when we are waiting for them
        if reply.body == "":
            self.logger.warning("Empty reply from device!")

        # Run parsing
        reply = self.parse_reply(cmd, reply)

        # Run type casting
        # This would work properly only between base Python types
        if not isinstance(reply, (int, float, str, bool)):
            self.logger.debug(
                "cast_reply_type()::complex data type <%s>, skipping casting.",
                type(reply),
            )
            return reply
        return self.cast_reply_type(cmd, reply)

    def parse_reply(self, cmd: Dict, reply: Any) -> str:
        """Overloaded method from base class. We need to do some more
        complex processing here for the status byte manipulations.
        """

        reply = self.check_errors(reply)
        self._last_status = ord(reply[0])
        self.logger.debug(
            "parse_reply()::status byte checked, invoking parsing on <%s>", reply[1:])

        return super().parse_reply(cmd, reply)

    def check_errors(self, reply: Any):
        """Checks if the first value is NACK or ACK.
        If it is NACK, there has been an error."""

        reply = reply.body
        if (reply[0] == self.reply_NACK):
            self.logger.debug(
                "check_errors():: NACK sent from pump, error.")
            raise SLDeviceInternalError
        elif (reply[0] == self.reply_ACK):
            self.logger.debug(
                "check_errors():: ACK sent from pump, no errors.")
            reply = parser.stripper(reply, prefix=self.reply_ACK)
            return reply

    def get_firmware_version(self) -> bool:
        """Gets the device's model and firmware version.
        """

        reply = self.send(self.cmd.GET_FIRMWARE)
        return reply

    def get_model(self) -> bool:
        """Gets the device's model and firmware version.
        """

        reply = self.send(self.cmd.GET_MODEL)
        return reply

    def get_status(self, operation: int):
        """
        Reads back pump status. TODO test
            Args:
                operation(int):
                    1: operation status
                    2: system status
                    3: run mode status
                    4: Dispense mode status
                    5: Reserved
                    6: Fault diagnosis"""

        cmd = self.cmd.GET_STATUS.copy()
        reply = self.send(cmd, str(operation))
        stripped_reply = reply.lstrip("0")

        if stripped_reply == "":
            stripped_reply = "0"

        reply_bin = format(int(stripped_reply), 'b')
        reply_bin = reply_bin.zfill(8)

        status_dict = self.cmd.OPERATION_STATUS.get(operation)

        status = ""
        status_bool = "FALSE"

        for count, key in enumerate(status_dict.keys()):
            if reply_bin[-(count+1)] == "0":
                status_bool = "FALSE"
            elif reply_bin[-(count+1)] == "1":
                status_bool = "TRUE"
            status += status_bool + " " + status_dict.get(key) + "; "

        return status

    def clear_errors(self):
        """Happens automatically upon errors read-out,
        except those requiring pump re-initialization.
        """

    def initialize_device(self):
        """Runs pump initialization."""

        cmd = self.cmd.INIT_PUMP.copy()

        self.send(cmd)
        self.logger.info("Device initialized.")

    @in_simulation_device_returns(True)
    def is_initialized(self) -> bool:
        """Check if pump has been initialized properly after power-up."""

    def is_idle(self):
        """Checks if pump is in idle state."""

    def is_connected(self):
        """Check communication. Returns pump address
        if communication works correctly"""

        cmd = self.cmd.COM_CHECK.copy()

        try:
            reply = self.send(cmd)
            self.logger.debug(
                f"is_connected()::Device connected; pump address is <{reply}>"
            )
            return True
        except SLConnectionError:
            return False

    def reset(self):
        """Brings the pump back to the factory settings, except the pump address.
        """

        cmd = self.cmd.RESET.copy()

        self.send(cmd)

    def start(self):
        """Starts program execution."""

        cmd = self.cmd.START.copy()

        self.send(cmd)

    def stop(self):
        """Stops pump immediately."""

        cmd = self.cmd.STOP.copy()

        self.send(cmd)

    def pause(self):
        """Pauses pump immediately."""

        cmd = self.cmd.PAUSE.copy()

        self.send(cmd)

    def prime(self):
        """Prime/Drain 1 stroke."""

        cmd = self.cmd.PRIME.copy()

        self.send(cmd)

    def get_mode(self):
        """Get dispensing mode"""

        cmd = self.cmd.GET_MODE.copy()
        mode = self.send(cmd)

        return self.cmd.MODES[mode]

    def get_speed(self):
        """Get flowrate in µL/min - for run mode"""

        cmd = self.cmd.GET_SPEED.copy()
        speed = self.send(cmd)

        return f"{speed} µL/min"

    def get_dispense_volume(self):
        """Current set value for
        dispense volume in µl
        """

        cmd = self.cmd.GET_DISPENSE_VOL.copy()
        volume = self.send(cmd)

        return f"{volume} µl"

    def get_dispense_time(self):
        """Gets the set value for the time to dispense a volume in dispense mode.
        Reported in seconds.
        """

        cmd = self.cmd.GET_TIME.copy()
        time = self.send(cmd)

        hours = int(time[:2])
        minutes = int(time[2:4])
        seconds = int(time[4:6])
        centiseconds = int(time[6:8])

        total_seconds = (hours*360) + (minutes*60) + seconds + (centiseconds/100)

        return f"{total_seconds} seconds"

    def get_cycles(self):
        """Gets the set number of dispense cycles."""

        cmd = self.cmd.GET_CYCLES.copy()
        cycles = self.send(cmd)

        if cycles in self.cmd.CYCLES:
            return self.cmd.CYCLES[cycles]
        else:
            return cycles

    def get_break_time(self):
        """Break time in seconds between dispense cycles."""

        cmd = self.cmd.GET_BREAK_TIME.copy()
        time = self.send(cmd)

        return f"{time} seconds"

    def get_time_counter(self):
        """Gets counter of actual run or dispense time.
        Reported in seconds.
        """

        cmd = self.cmd.GET_TIME_COUNTER.copy()
        time = self.send(cmd)

        hours = int(time[:2])
        minutes = int(time[2:4])
        seconds = int(time[4:6])
        centiseconds = int(time[6:8])

        total_seconds = (hours*360) + (minutes*60) + seconds + (centiseconds/100)

        return f"{total_seconds} seconds"

    def get_volume_counter(self):
        """Gets Dispensed volume since last pump start in ml"""

        cmd = self.cmd.GET_VOL_COUNTER.copy()
        volume = self.send(cmd)

        return f"{volume} µl"

    def get_profile(self):
        """Gets liquids profile from the pump"""

        cmd = self.cmd.GET_PROFILE.copy()

        profile = self.send(cmd)
        return self.cmd.PROFILES[profile]

    def get_calibration_factor(self):
        """Gets calibration factor for pump stroke volume from the pump, as a %"""

        cmd = self.cmd.GET_CALIBRATION_FACTOR.copy()
        calibration = self.send(cmd)

        return f"{float(calibration)/100} %"

    def get_pump_address(self):
        """Gets the pump address for serial
        interface commands.
        """

        cmd = self.cmd.GET_ADDRESS.copy()
        _switch_address = self.send(cmd)
        # TODO check address is between 00 and 99
        self._switch_address = _switch_address

        return self._switch_address

    def set_pump_address(self, address: int):
        """Sets the pump address for serial
        interface commands.
        """
        # TODO this is not working properly, fix it

        cmd = self.cmd.SET_ADDRESS.copy()
        _swicth_address = str(address).rjust(2, "0")
        reply = self.send(cmd, str(address))
        # TODO check address is between 00 and 99
        self._switch_address = _swicth_address

        return reply

    def set_run_mode(self):
        """Sets the pump to run mode."""

        cmd = self.cmd.SET_RUN_MODE.copy()

        self.send(cmd)

    def set_dispense_mode(self):
        """Sets the pump to dispense mode mL and time active."""

        cmd = self.cmd.SET_DISPENSE_MODE.copy()

        self.send(cmd)

    def set_dispense_mode_ml_min(self):
        """Sets the pump to dispense mode mL/min and time active."""

        cmd = self.cmd.SET_DISPENSE_MODE_ML_MIN.copy()

        self.send(cmd)

    def set_speed(self, speed: int):
        """Sets flow rate in µL/min - requires run mode."""
        # TODO - test

        if self.get_mode() != 'Run mode active':
            self.logger.debug(
                "Pump not in correct mode for this command - needs to be in run mode"
            )
            raise SLDeviceCommandError

        cmd = self.cmd.SET_SPEED.copy()

        self.send(cmd, str(speed))

    def set_dispense_volume(self, volume: int):
        """Sets the value for the dispense volume - requires dispense mode mL and time active.
        The unit is µl.
        """
        # TODO - test & check if this works in other dispense mode as well
        if self.get_mode() != 'Dispense mode mL and time active':
            self.logger.debug(
                "Pump not in correct mode-needs to be in dispense mode mL and time active")
            raise SLDeviceCommandError

        cmd = self.cmd.SET_DISPENSE_VOL.copy()

        self.send(cmd, str(volume))

    def set_cycles(self, cycles: int):
        """The number of cycles that the given volume shall
        be dispensed, is defined. Values from 1-999. 1000 infinite
        number of repetitions"""

        # TODO - test & check if this works in other dispense mode as well
        if self.get_mode() != 'Dispense mode mL and time active':
            self.logger.debug(
                "Pump not in correct mode-needs to be in dispense mode mL and time active")
            raise SLDeviceCommandError

        cmd = self.cmd.SET_CYCLES.copy()

        self.send(cmd, str(cycles))

    def set_time(self, time: int):
        """Sets the value for the time to dispense a volume in seconds
        - requires dispense mode mL and time active"""

        # TODO - test & check if this works in other dispense mode as well
        if self.get_mode() != 'Dispense mode mL and time active':
            self.logger.debug(
                "Pump not in correct mode for this command - needs to be in dispense mode mL and time active"
            )
            raise SLDeviceCommandError

        # Convert seconds into hhmmssss format
        centiseconds_decimal = time % 1
        centiseconds = centiseconds_decimal*100
        seconds_all = int(time//1)
        seconds = seconds_all % 60
        minutes_all = (seconds_all-seconds)/60
        minutes = minutes_all % 60
        hours = (minutes_all-minutes)/60

        full_time = (
            str(int(hours)).rjust(2, "0")
            + str(int(minutes)).rjust(2, "0")
            + str(int(seconds)).rjust(2, "0")
            + str(int(centiseconds)).rjust(2, "0")
        )

        self.logger.info(f"Setting time: {full_time}")

        cmd = self.cmd.SET_TIME.copy()

        self.send(cmd, str(full_time))

    def set_break_time(self, time: int):
        """Break time between two programmed dispense
        cycles."""

        # TODO - test & check if this works in other dispense mode as well
        if self.get_mode() != 'Dispense mode mL and time active':
            self.logger.debug(
                "Pump not in correct mode for this command - needs to be in dispense \
                    mode mL and time active")
            raise SLDeviceCommandError

        cmd = self.cmd.SET_BREAK_TIME.copy()

        self.send(cmd, time)

    def set_profile(self, profile: int):
        """Sets liquid profile.
        Args:
            profile(int):
                    0: standard
                    1: volatile
                    2: viscous
                    3: highly viscous
                    4: Reserved
        """

        cmd = self.cmd.SET_PROFILE.copy()

        self.send(cmd, str(profile))

    def set_calibration_factor(self, factor: int):
        """Sets calibration factor for pump stroke volume as %"""

        cmd = self.cmd.SET_CALIBRATION_FACTOR.copy()
        # percentage is sent as the % value * 100
        factor = factor*100

        self.send(cmd, int(factor))

    def withdraw(self):
        """Here to comply with abstract classes. TODO Re-think
        abstract for diapgragm pumps"""

    def dispense(self):
        """Here to comply with abstract classes. TODO Re-think
        abstract for diapgragm pumps"""
