from collections import namedtuple
from typing import Optional, Tuple

from pylabware.connections import ModbusCommandType
from pylabware.controllers import (
    AbstractTemperatureController,
    in_simulation_device_returns,
)
from pylabware.exceptions import SLDeviceCommandError, SLDeviceError
from pylabware.models import ConnectionParameters, LabDeviceCommands, LabDeviceReply


class PolarBearPlusConstants:
    """
    Default Constants used for the connecting to the
    PolarBearPlus unit
    """

    # Defaults
    PolarBearAddress = "192.168.1.90"
    PolarBearPort = 502
    BalanceAddress = "192.168.111.102"
    BalancePort = 8001
    UnitId = 255
    RoomTemperature = 21


class PolarBearPlusRegisterConstants:
    """
    Resgister Constants used for the connecting to the
    polarbearplus unit
    """

    _Register = namedtuple("_Register", "address bits")

    # Set Point addresses
    TARGET_SET_POINT = _Register(address=769, bits=None)
    STIRRER_SPEED = _Register(address=514, bits=None)

    # PV addresses
    PLATE_TEMPERATURE = _Register(address=256, bits=None)
    HEATER_TEMPERATURE = _Register(address=260, bits=None)
    MASTER_TEMPERATURE = _Register(address=264, bits=None)
    COMPRESSOR_TEMPERATURE = _Register(address=268, bits=None)

    # Alarm addresses
    PLATE_ALARM = _Register(address=6219, bits=None)
    HEATER_ALARM = _Register(address=6347, bits=None)
    MASTER_ALARM = _Register(address=6475, bits=None)
    COMPRESSOR_ALARM = _Register(address=6603, bits=None)

    # Digital input addresses
    TEMP_CONTROL_SWITCH = _Register(address=5441, bits=None)
    STIRRER_CONTROL_SWITCH = _Register(address=5409, bits=None)

    # Relays
    INTERNAL_STIRRER_RELAY = _Register(address=5457, bits=None)
    EXTERNAL_STIRRER_RELAY = _Register(address=5743, bits=None)

    # Stirrer stype
    STIRRER_TYPE = _Register(address=11948, bits=None)

    # Output values
    HEATER_OUTPUT = _Register(address=779, bits=None)
    COOLING_OUTPUT = _Register(address=780, bits=None)
    BALANCE_OUTPUT = _Register(address=11973, bits=None)
    BALANCE_DECIMAL_OUTPUT = _Register(address=11968, bits=None)

    TEMPERATURE_CONTROL = _Register(address=336, bits=None)


class PolarBearPlusCommands(LabDeviceCommands):
    """Collection of command definitions for PolarBearPlus."""

    # Commands
    WRITE_TARGET_TEMP = {
        "name": "WRITE_TARGET_TEMP",
        "command_type": ModbusCommandType.WRITE_REGISTER,
        "address": PolarBearPlusRegisterConstants.TARGET_SET_POINT.address,
        "unit_id": PolarBearPlusConstants.UnitId,
    }

    WRITE_TARGET_STIR_SPEED = {
        "name": "WRITE_TARGET_STIR_SPEED",
        "command_type": ModbusCommandType.WRITE_REGISTER,
        "address": PolarBearPlusRegisterConstants.STIRRER_SPEED.address,
        "check": {"min": 0, "max": 1500},
        "unit_id": PolarBearPlusConstants.UnitId,
    }

    WRITE_STIRRER_TYPE = {
        "name": "WRITE_STIRRER_TYPE",
        "command_type": ModbusCommandType.WRITE_REGISTER,
        "address": PolarBearPlusRegisterConstants.STIRRER_TYPE.address,
        "unit_id": PolarBearPlusConstants.UnitId,
    }

    READ_TEMPERATURE_SP = {
        "name": "READ_TEMPERATURE_SP",
        "command_type": ModbusCommandType.READ_HOLDING_REGISTERS,
        "address": PolarBearPlusRegisterConstants.TARGET_SET_POINT.address,
        "unit_id": PolarBearPlusConstants.UnitId,
        "reply": {"type": int},
    }

    READ_STIRRER_SP = {
        "name": "READ_STIRRER_SP",
        "command_type": ModbusCommandType.READ_HOLDING_REGISTERS,
        "address": PolarBearPlusRegisterConstants.STIRRER_SPEED.address,
        "unit_id": PolarBearPlusConstants.UnitId,
        "reply": {"type": int},
    }

    READ_HEATER_POWER = {
        "name": "READ_HEATER_POWER",
        "command_type": ModbusCommandType.READ_HOLDING_REGISTERS,
        "address": PolarBearPlusRegisterConstants.HEATER_OUTPUT.address,
        "unit_id": PolarBearPlusConstants.UnitId,
        "reply": {"type": int},
    }

    READ_COOLER_POWER = {
        "name": "READ_COOLER_POWER",
        "command_type": ModbusCommandType.READ_HOLDING_REGISTERS,
        "address": PolarBearPlusRegisterConstants.COOLING_OUTPUT.address,
        "unit_id": PolarBearPlusConstants.UnitId,
        "reply": {"type": int},
    }

    # Get Alarm status
    READ_PLATE_ALARM = {
        "name": "READ_PLATE_ALARM",
        "command_type": ModbusCommandType.READ_HOLDING_REGISTERS,
        "address": PolarBearPlusRegisterConstants.PLATE_ALARM.address,
        "unit_id": PolarBearPlusConstants.UnitId,
        "reply": {"type": int},
    }

    READ_HEATER_ALARM = {
        "name": "READ_HEATER_ALARM",
        "command_type": ModbusCommandType.READ_HOLDING_REGISTERS,
        "address": PolarBearPlusRegisterConstants.HEATER_ALARM.address,
        "unit_id": PolarBearPlusConstants.UnitId,
        "reply": {"type": int},
    }

    READ_MASTER_ALARM = {
        "name": "READ_MASTER_ALARM",
        "command_type": ModbusCommandType.READ_HOLDING_REGISTERS,
        "address": PolarBearPlusRegisterConstants.MASTER_ALARM.address,
        "unit_id": PolarBearPlusConstants.UnitId,
        "reply": {"type": int},
    }

    READ_COMPRESSOR_ALARM = {
        "name": "READ_COMPRESSOR_ALARM",
        "command_type": ModbusCommandType.READ_HOLDING_REGISTERS,
        "address": PolarBearPlusRegisterConstants.COMPRESSOR_ALARM.address,
        "unit_id": PolarBearPlusConstants.UnitId,
        "reply": {"type": int},
    }

    READ_COMPRESSOR_ALARM_STATUS = {
        "name": "READ_COMPRESSOR_ALARM_STATUS",
        "command_type": ModbusCommandType.READ_HOLDING_REGISTERS,
        "address": PolarBearPlusRegisterConstants.COMPRESSOR_ALARM.address,
        "unit_id": PolarBearPlusConstants.UnitId,
        "reply": {"type": int},
    }

    # Relay switches
    READ_TEMPERATURE_CONTROL_SWITCH = {
        "name": "READ_TEMPERATURE_CONTROL_SWITCH",
        "command_type": ModbusCommandType.READ_HOLDING_REGISTERS,
        "address": PolarBearPlusRegisterConstants.TEMP_CONTROL_SWITCH.address,
        "unit_id": PolarBearPlusConstants.UnitId,
        "reply": {"type": int},
    }

    READ_STIRRER_CONTROL_SWITCH = {
        "name": "READ_STIRRER_CONTROL_SWITCH",
        "command_type": ModbusCommandType.READ_HOLDING_REGISTERS,
        "address": PolarBearPlusRegisterConstants.STIRRER_CONTROL_SWITCH.address,
        "unit_id": PolarBearPlusConstants.UnitId,
        "reply": {"type": int},
    }

    # Get temperatures
    READ_PLATE_TEMPERATURE = {
        "name": "READ_PLATE_TEMPERATURE",
        "command_type": ModbusCommandType.READ_HOLDING_REGISTERS,
        "address": PolarBearPlusRegisterConstants.PLATE_TEMPERATURE.address,
        "unit_id": PolarBearPlusConstants.UnitId,
        "reply": {"type": int},
    }

    READ_HEATER_TEMPERATURE = {
        "name": "READ_HEATER_TEMPERATURE",
        "command_type": ModbusCommandType.READ_HOLDING_REGISTERS,
        "address": PolarBearPlusRegisterConstants.HEATER_TEMPERATURE.address,
        "unit_id": PolarBearPlusConstants.UnitId,
        "reply": {"type": int},
    }

    READ_MASTER_TEMPERATURE = {
        "name": "READ_MASTER_TEMPERATURE",
        "command_type": ModbusCommandType.READ_HOLDING_REGISTERS,
        "address": PolarBearPlusRegisterConstants.MASTER_TEMPERATURE.address,
        "unit_id": PolarBearPlusConstants.UnitId,
        "reply": {"type": int},
    }

    READ_COMPRESSOR_TEMPERATURE = {
        "name": "READ_COMPRESSOR_TEMPERATURE",
        "command_type": ModbusCommandType.READ_HOLDING_REGISTERS,
        "address": PolarBearPlusRegisterConstants.COMPRESSOR_TEMPERATURE.address,
        "unit_id": PolarBearPlusConstants.UnitId,
        "reply": {"type": int},
    }


class PolarBearPlus(AbstractTemperatureController):
    def __init__(self, device_name: str, connection_mode: str, address: str, port: int):

        self.cmd = PolarBearPlusCommands

        if connection_mode != "modbustcp":
            raise SLDeviceError("device support only tco modbus connection")

        connection_parameters: ConnectionParameters = {
            "port": port,
            "address": address,
        }

        super().__init__(device_name, connection_mode, connection_parameters)

    def _send_heartbeat_msg(self):
        """
        Dummy function to keep connection alive. Reads the compressor temperature
        """
        self._read(self.cmd.READ_COMPRESSOR_TEMPERATURE)

    def _read(self, cmd: dict) -> int:
        return self.send(cmd=cmd)[0]

    def _validate_command_msg(self, cmd: dict, raise_exception=True) -> bool:
        if not cmd.keys() >= {"address", "command_type"}:
            if raise_exception:
                raise SLDeviceCommandError(
                    "Key error, command msg should have keys 'address' and 'command_type'"
                )

            return False

        if not isinstance(cmd["address"], int):
            if raise_exception:
                raise SLDeviceCommandError(
                    "Address type error. Address property should be an integer"
                )

            return False

        if not isinstance(cmd["command_type"], ModbusCommandType):
            if raise_exception:
                raise SLDeviceCommandError(
                    "command_type type error. command_type property should be an instance of ModbusCommandType"
                )

            return False

        return True

    def prepare_message(self, cmd: dict, value: Optional[int]) -> dict:  # type: ignore

        self._validate_command_msg(cmd)

        msg_for_connection = {
            "address": cmd["address"],
            "command_type": cmd["command_type"],
            "unit": cmd["unit_id"],
        }

        if value is not None:
            msg_for_connection["value"] = value

        return msg_for_connection

    @in_simulation_device_returns(0)
    def is_idle(self):
        """Checks whether the device is in idle state."""
        return True  # FIXME Add a proper is_idle state

    def is_connected(self):
        return self.connection.is_connection_open()

    def parse_reply(self, cmd: dict, reply: LabDeviceReply) -> list:
        return reply.body

    def get_status(self) -> dict:
        """Gets device internal status.

        Returns:
            (dict): Alarm status for the plate, heater,
            master and compressor
        """

        status = {}

        status["plate_status"] = self._read(self.cmd.READ_PLATE_ALARM)
        status["heater_status"] = self._read(self.cmd.READ_HEATER_ALARM)
        status["master_status"] = self._read(self.cmd.READ_MASTER_ALARM)
        status["compressor_status"] = self._read(self.cmd.READ_COMPRESSOR_ALARM)

        return status

    def check_errors(self):
        """Gets errors from the device"""

    def clear_errors(self):
        """Clear errors in device"""

    def initialize_device(self):
        """the method is prepering device for a work"""
        self.start_task(interval=10, method=self._send_heartbeat_msg)

    def set_temperature(self, temperature: float, sensor: Optional[int] = None) -> None:
        """Sets desired temperature.

        Args:
            temperature (float): Temperature setpoint in °C.
        """
        if temperature < 0:
            new_temperature = 65536 + (temperature * 100)
            self.send(self.cmd.WRITE_TARGET_TEMP, new_temperature)

        else:
            new_temperature = temperature * 100
            self.send(self.cmd.WRITE_TARGET_TEMP, new_temperature)

    def set_speed(self, speed: float) -> None:
        """Sets desired stirrer speed.

        Args:
            speed (float): Speed in RPM
        """

        self.send(self.cmd.WRITE_TARGET_STIR_SPEED, speed)

    def start_stirring(self) -> None:
        """Starts stirring, however Polar bear does not support this funcion,
        so it will return
        """

        return

    def stop_stirring(self) -> None:
        """Stops stirring, however Polar bear does not support this funcion,
        so it will set_speed to 0 RPM
        """
        self.set_speed(0)

    def set_stirrer_type(self, stirrer_type: int = 1) -> None:
        """Sets desired stirrer stype attached to the PolarBear.

        Args:
            type (int): type of stirrer in the PolarBear:
                1: magnetic stirring (default)
                2: overhead small stirring
                3: overhead large stitting
        """

        self.send(self.cmd.WRITE_STIRRER_TYPE, stirrer_type)

    def get_temperature_power(self) -> Tuple[int, int]:
        """Gets the power that is used for eating and cooling.

        Returns:
            tuple (int,int): %power used for heater, cooler

        """

        heater_output = self._read(self.cmd.READ_HEATER_POWER)
        heater_power = heater_output / 100

        cooling_output = self._read(self.cmd.READ_COOLER_POWER)
        cooling_power = cooling_output / 100

        return heater_power, cooling_power

    def start_temperature_regulation(self) -> None:
        """Starts temperature.

        Currently this is controlled with external switches in
        PolarBearPlus

        Args:
        """
        if self.get_temperature_control_switch():
            return True
        else:
            SLDeviceError(
                "Left switch is off in the instrument, \
            cannot start heating/cooling"
            )

    def stop_temperature_regulation(self) -> None:
        """Stops temperature.

        Currently this is controlled with external switches in
        PolarBearPlus. However, before the unit can be turned off,
        the temperature has to be set to ambient temperature

        Args:
        """

        self.set_temperature(temperature=PolarBearPlusConstants.RoomTemperature)

    def get_temperature(self, sensor: int = 3) -> float:
        """
        Gets the current temperature of the specified sensor

        Args:
            sensor(int):
                1: Plate temperature
                2: Heater temperature, heating element
                3: Master temperature, external probe (default)
                4: Compressor temeprature
        Returns:
            float: temperature of the sensor
        """

        if sensor == 1:
            temperature = self._read(self.cmd.READ_PLATE_TEMPERATURE)
            return temperature / 100
        elif sensor == 2:
            temperature = self._read(self.cmd.READ_HEATER_TEMPERATURE)
            return temperature / 100
        elif sensor == 3:
            temperature = self._read(self.cmd.READ_MASTER_TEMPERATURE)
            return temperature / 100
        elif sensor == 4:
            temperature = self._read(self.cmd.READ_COMPRESSOR_TEMPERATURE)
            return temperature / 100

    def get_temperature_setpoint(self, sensor: int = 3) -> float:
        """
        Gets the temperature SP for the specified sensor

        Args:
            sensor(int):
                1: Plate temperature
                2: Heater temperature, heatiing element
                3: Master temperature, external probe (default)
                4: Compressor temeprature
        Returns:
            (float) SP temperature for the sensor in Celcius
        """
        return self._read(self.cmd.READ_TEMPERATURE_SP) / 100

    @in_simulation_device_returns([0, 0])
    def get_temperature_control_switch(self) -> bool:
        """
        Determines if the temeprature control switch is on on the
        side on the instrument.

        (int): 0: off, 1: on

        Returns:
            True if on, False if off
        """

        status = self._read(self.cmd.READ_TEMPERATURE_CONTROL_SWITCH)

        if status == 0:
            return False
        else:
            return True

    def get_stirrer_control_switch(self) -> bool:
        """
        Determines if the stirrer control switch is on on the
        side on the instrument

        (int): 0: on, 1: off

        Returns:
            True if on, False if off
        """

        status = self._read(self.cmd.READ_STIRRER_CONTROL_SWITCH)

        if status == 0:
            return True
        else:
            return False
