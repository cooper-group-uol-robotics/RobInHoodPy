"""MT_XPR To do list:

    1. Implement simulations mode
    2. Add a value parser for returning dictionaries - maybe use the example in utils
    3. Add value checking
    4. Add results protocols
    5. Add tolerance profile, result out of tolerance checking, head-reading, head-writing
    6. Improve dispense method to factor in errors and error recovery where possible.
    7. Currently when taring sometimes get a StaticDetectionFailed error - still tares """

from __future__ import annotations
import base64
from backports.pbkdf2 import pbkdf2_hmac
from Cryptodome.Cipher import AES
import time

# Core imports
from ..controllers import AbstractSolidDispensing
from ..models import ConnectionParameters, LabDeviceCommands


class XPR226DRQCommands(LabDeviceCommands):
    """Collection of command definitions for Mettler Toledo XPR226 DRQ balance.
    These commands are based on the english section of the manufacturers user manual,
    version XXX TODO.
    """

    DEFAULT_NAME = "mettler_xpr226_drq"

    # ################### Control commands ###################################

    OPEN_SESSION = {
        "name": "OPEN_SESSION",
        "service": "ISessionService",
        "method": "OpenSession"}

    WAKE_FROM_STANDBY = {
        "name": "WAKE_BALANCE",
        "service": "IBasicService",
        "method": "WakeupFromStandby",
        "reply": {"type": dict}}

    MOVE_DOOR = {
        "name": "MOVE_DOOR",
        "service": "IDraftShieldsService",
        "method": "SetPosition",
        "element_name": "SetPositionRequest",  # TODO check if this is needed
        "reply": {"type": dict}}

    ZERO_BALANCE = {
        "name": "ZERO_BALANCE",
        "service": "IWeighingService",
        "method": "Zero",
        "reply": {"type": dict}}

    TARE_BALANCE = {
        "name": "TARE_BALANCE",
        "service": "IWeighingService",
        "method": "Tare",
        "reply": {"type": dict}}

    GET_WEIGHT = {
        "name": "GET_WEIGHT",
        "service": "IWeighingService",
        "method": "GetWeight",
        "reply": {"type": dict}}

    START_TASK = {
        "name": "START_TASK",
        "service": "IWeighingTaskService",
        "method": "StartTask",
        "reply": {"type": dict}}

    RUN_DOSING_JOB = {
        "name": "RUN_DOSING_JOB",
        "service": "IDosingAutomationService",
        "method": "StartExecuteDosingJobListAsync",
        "reply": {"type": dict}}

    GET_NOTIFICATION = {
        "name": "GET_NOTIFICATION",
        "service": "INotificationService",
        "method": "GetNotifications",
        "reply": {"type": dict}}

    CONFIRM_DOSING_JOB = {
        "name": "CONFIRM_DOSING_JOB",
        "service": "IDosingAutomationService",
        "method": "ConfirmDosingJobAction",
        "reply": {"type": dict}}


class XPR226DRQ(AbstractSolidDispensing):
    """
    This provides a Python class for the Mettler Toledo XPR 226 DRQ
    balance based on the english section of the original
    operation manual XXX TODO Add manual.
    """

    def __init__(
        self,
        device_name: str,
        connection_mode: str,
        socket: str,
     ) -> None:
        """Default constructor"""

        # Load commands from helper class
        self.cmd = XPR226DRQCommands

        # Connection settings
        connection_parameters: ConnectionParameters = {}
        # Change any connection settings to device specific ones, if needed
        connection_parameters["wsdl_name"] = "MT.Laboratory.Balance.XprXsr.V02.wsdl"
        connection_parameters["password"] = "112358"
        connection_parameters["socket"] = socket
        connection_parameters["binding"] = "BasicHttpBinding_"

        super().__init__(
            device_name, connection_mode, connection_parameters)

        # Protocol settings - not sure if I need any of these
        # Terminator for the command string (from host to device)
        self.command_terminator = None
        # Terminator for the reply string (from device to host)
        self.reply_terminator = None
        # Separator between command and command arguments, if any
        self.args_delimiter = None
        # Will be none if the device is not initialized.
        self.session_id = None

    def _decode_base64(self, base64_encrypted_string: str) -> bytes:
        """Converts a base 64 string into bytes"""
        message_bytes = base64.b64decode(base64_encrypted_string)

        return message_bytes

    def _compute_key_from_password(self, password: str, salt_bytes: bytes) -> bytes:
        """Creates a key of 32 byte length based on salt and password"""
        password_data = password.encode("utf8")
        # 32 bytes used, despite manual suggesting 16 bytes
        key_bytes = pbkdf2_hmac("sha1", password_data, salt_bytes, 1000, 32)

        return key_bytes

    def _decrypt_ecb(self, key_bytes: bytes, data_bytes: bytes) -> str:
        """Electronic code book. Decrypts session_id into a byte string, and decoded
        back into a string (utf-8 encoding)."""

        cipher = AES.new(key_bytes, AES.MODE_ECB)
        plain_text = cipher.decrypt(data_bytes)

        # Strip trainling new lines
        return plain_text.decode("utf-8").strip()

    def _decrypt_session_id(
            self,
            encrypted_session_id: str,
            encrypted_salt: str,
            password: str
    ) -> str:
        """Decrypts session ID"""

        salt_data = self._decode_base64(encrypted_salt)
        session_id_data = self._decode_base64(encrypted_session_id)
        _key = self._compute_key_from_password(password, salt_data)
        session_id = self._decrypt_ecb(_key, session_id_data)

        return session_id

    def initialize_device(self):
        """Opens a session with the device"""

        cmd_dict = {
            "method": self.cmd.OPEN_SESSION["method"],
            "service": self.cmd.OPEN_SESSION["service"],
            "reply": True}

        response_object = self.send(cmd_dict)
        encrypted_response = response_object.body

        self.session_id = self._decrypt_session_id(
            encrypted_response["SessionId"],
            encrypted_response["Salt"],
            self.connection.password)

    def wakeup(self):
        """Wakes the balance up from standby."""

        # FIXME
        if self.session_id is None:
            return "Device must be initialised"

        cmd_dict = {
            "method" : self.cmd.WAKE_FROM_STANDBY["method"],
            "service" : self.cmd.WAKE_FROM_STANDBY["service"],
            "reply": True,
            "message_list" : [self.session_id]}

        response_object = self.send(cmd_dict)
        return_dict = response_object.body

        return return_dict

    def tare(self):
        """Tares the balance."""

        # FIXME
        if self.session_id is None:
            return "Device must be initialised"

        cmd_dict = {
            "method" : self.cmd.TARE_BALANCE["method"],
            "service" : self.cmd.TARE_BALANCE["service"],
            "reply" : True,
            "message_list" : [self.session_id]}

        response_object = self.send(cmd_dict)
        return_dict = response_object.body

        return return_dict

    def zero(self):
        """Zeros the balance."""

        # FIXME
        if self.session_id is None:
            return "Device must be initialised"

        cmd_dict = {
            "method" : self.cmd.ZERO_BALANCE["method"],
            "service" : self.cmd.ZERO_BALANCE["service"],
            "reply": True,
            "message_list" : [self.session_id]}

        response_object = self.send(cmd_dict)
        return_dict = response_object.body

        return return_dict

    # FIXME
    def open_door(self):
        """Opens the balance doors."""

        if self.session_id is None:
            return "Device must be initialised"

        cmd_dict_left = {
            "method" : self.cmd.MOVE_DOOR["method"],
            "service" : self.cmd.MOVE_DOOR["service"],
            "reply" : True,
            "message_list" : [self.session_id, {
                                "DraftShieldPosition" : {
                                    "DraftShieldId": "LeftOuter",
                                    "OpeningWidth": 100}}]}

        cmd_dict_right = {
            "method" : self.cmd.MOVE_DOOR["method"],
            "service" : self.cmd.MOVE_DOOR["service"],
            "reply" : True,
            "message_list" : [self.session_id, {
                                "DraftShieldPosition" : {
                                    "DraftShieldId": "RightOuter",
                                    "OpeningWidth": 100}}]}

        response_object_left = self.send(cmd_dict_left)
        response_object_right = self.send(cmd_dict_right)

        return_dict_left = response_object_left.body
        return_dict_right = response_object_right.body

        # FIXME is this needed?
        return return_dict_left, return_dict_right

    def close_door(self):
        """opens the balance doors."""

        if self.session_id is None:
            return "Device must be initialised"

        cmd_dict_left = {
            "method" : self.cmd.MOVE_DOOR["method"],
            "service" : self.cmd.MOVE_DOOR["service"],
            "reply" : True,
            "message_list" : [self.session_id, {
                                "DraftShieldPosition" : {
                                    "DraftShieldId": "LeftOuter",
                                    "OpeningWidth": 0}}]}

        cmd_dict_right = {
            "method" : self.cmd.MOVE_DOOR["method"],
            "service" : self.cmd.MOVE_DOOR["service"],
            "reply" : True,
            "message_list" : [self.session_id, {
                                "DraftShieldPosition" : {
                                    "DraftShieldId": "RightOuter",
                                    "OpeningWidth": 0}}]}

        response_object_left = self.send(cmd_dict_left)
        response_object_right = self.send(cmd_dict_right)

        return_dict_left = response_object_left.body
        return_dict_right = response_object_right.body

        # FIXME is this needed?
        return return_dict_left, return_dict_right

    def get_weight(self):
        """Gets the weight currently on the balance."""

        if self.session_id is None:
            return "Device must be initialised"

        cmd_dict = {
            "method" : self.cmd.GET_WEIGHT["method"],
            "service" : self.cmd.GET_WEIGHT["service"],
            "reply": True,
            "message_list" : [self.session_id]}

        response_object = self.send(cmd_dict)
        return_dict = response_object.body

        print(return_dict)

    def _start_task(self, method_name: str):
        """Part of the automated dosing method.
        Starts an automated weighing task with a weighing method
        named method_name.
            Args:
                method_name (str): method on the XPR balance."""

        cmd_dict = {
            "method" : self.cmd.START_TASK["method"],
            "service" : self.cmd.START_TASK["service"],
            "reply": True,
            "message_list" : [self.session_id, method_name]}

        response_object = self.send(cmd_dict)
        return_dict = response_object.body

        return return_dict

    def _run_dosing_job(self, substance_name: str, dispense_mass: float, tolerance: int = 10):
        """Starts executing a dosing job.
            Args:
                substance_name (str): name of dispense head - case sensitive
                dispense_mass (float): mass required
                tolerance (int): percentage"""
        # FIXME handling errors

        if self.session_id is None:
            return "Device must be initialised"

        cmd_dict = {
            "method": self.cmd.RUN_DOSING_JOB["method"],
            "service": self.cmd.RUN_DOSING_JOB["service"],
            "reply": True,
            "message_list": [self.session_id,
                             {"DosingJob" : {
                                "SubstanceName": substance_name,
                                "VialName": "Vial1",
                                "TargetWeight": {"Unit": "Milligram", "Value": dispense_mass},
                                "LowerTolerance" : {"Unit" : "Percent", "Value" : tolerance},
                                "UpperTolerance" : {"Unit" : "Percent", "Value" : tolerance}}}]}

        response_object = self.send(cmd_dict)
        return_dict = response_object.body

        return return_dict

    def _handle_notification(self, notification: dict):
        """Handles notifications that are produced by the balance during an automatic dispense."""
        # TODO expand notifications expected past bare minimum.

        notification_out = {}
        notification_type = list(notification.keys())[0]

        if notification_type == "DosingAutomationJobFinishedAsyncNotification":

            notification_out["Outcome"] = notification[notification_type]["Outcome"]
            notification_out["Substance Name"] = notification[notification_type]["DosingResult"]["DosingJob"]["SubstanceName"]
            notification_out["Target Weight"] = {
                "Value": float(notification[notification_type]["DosingResult"]["DosingJob"]["TargetWeight"]["Value"]),
                "Unit": notification[notification_type]["DosingResult"]["DosingJob"]["TargetWeight"]["Unit"]}
            notification_out["Tolerance"] = {
                "Value": float(notification[notification_type]["DosingResult"]["DosingJob"]["LowerTolerance"]["Value"]),
                "Unit": notification[notification_type]["DosingResult"]["DosingJob"]["TargetWeight"]["Unit"]}
            notification_out["Net Weight"] = notification[notification_type]["DosingResult"]["WeightSample"]["NetWeight"]

            return True, notification_out

        elif notification_type == "DosingAutomationFinishedAsyncNotification":
            return True, None

        elif notification_type == "DosingAutomationActionAsyncNotification":
            dosing_job_action_type = notification["DosingAutomationActionAsyncNotification"]["DosingJobActionType"]
            dosing_job_action_item = notification["DosingAutomationActionAsyncNotification"]["ActionItem"]

            cmd_dict = {
                "method": self.cmd.CONFIRM_DOSING_JOB["method"],
                "service": self.cmd.CONFIRM_DOSING_JOB["service"],
                "message_list": [self.session_id, dosing_job_action_type, dosing_job_action_item]}

            self.send(cmd_dict, None)

            return False, None

        else:
            print("Unhandled notification: " + notification_type)

            return False, None

    def _get_notification(self) -> dict:
        """ Part of the automated dosing method.
        Gets notifications from the balance that are produced during automatic weighing. Passes notifications to
        _handle_notifications. Currently has a 120 second timeout, with a check rate of 10 seconds.
        Returns a notifications_out dictionary"""

        if self.session_id is None:
            return "Device must be initialised"

        notifications_out = {}
        done = False
        timer = 0

        while timer < 12:

            cmd_dict = {
                "method": self.cmd.GET_NOTIFICATION["method"],
                "service": self.cmd.GET_NOTIFICATION["service"],
                "reply": True,
                "message_list": [self.session_id]}

            response_object = self.send(cmd_dict)
            return_dict = response_object.body
            all_notifications = return_dict["Notifications"]

            if not done:
                if not all_notifications:
                    for element in all_notifications["_value_1"]:
                        break_flag, res = self._handle_notification(element)
                        notifications_out["job finished"] = res
                    timer += 1
                else:
                    print(f"Waiting for notifications {timer*10} seconds elapsed")
                    timer += 1
                time.sleep(10)
            else:
                break

        return notifications_out

    def dispense(self, task_name: str, substance_name: str, amount: float, tolerance: int):
        """Combined method for all of the necessary steps to start a doing job"""

        if self.session_id is None:
            return "Device should be initialised"

        self._start_task(task_name)
        self._run_dosing_job(substance_name, amount, tolerance)
        return_dict = self._get_notification()

        return return_dict

    def parse_reply(self, msg, reply):
        """TODO Add functionality"""
        return reply

    def prepare_message(self, cmd_dict):
        """Prepares message to be sent via SOAP command"""

        service_object = self.connection.create_service(cmd_dict["service"])

        if "message_list" in cmd_dict.keys():
            message = {
                "service_object": service_object,
                "method": cmd_dict["method"],
                "message_list": cmd_dict["message_list"]}
        else:
            message = {
                "service_object": service_object,
                "method": cmd_dict["method"]}

        return message

    def is_connected(self):
        """Not supported on this device"""

    def is_idle(self):
        """Not supported on this device"""

    def get_status(self):
        """Not supported on this device"""

    def check_errors(self):
        """Not supported on this device"""

    def clear_errors(self):
        """Not supported on this device"""

    def start(self):
        """Not supported on this device"""

    def stop(self):
        """Not supported on this device"""
