import sys
import os

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__))+'/..')

import serial
import time
import logging
from config.configuration import *
from .camera import CameraCapper

class Arduino():
    def __init__(self,port=FILTERINGSTATION_PORT, camera_id=0):
        self.capper = serial.Serial(port=port, baudrate=9600)
        time.sleep(2)
        #self.camera_id= camera_id
        self._logger = logging.getLogger("Capper")
    def vacuum_on(self):
        self._logger.info("Vacuum on")
        self.capper.write(b'4')
    def vacuum_off(self):
        self._logger.info("Vacuum off")
        self.capper.write(b'5')