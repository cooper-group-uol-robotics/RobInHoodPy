import sys
import os

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__))+'/..')

import serial
import time
import logging
from config.configuration import *
from .camera import CameraCapper

class Capper():
    def __init__(self,port=CAPPER_PORT, camera_id=0):
        self.capper = serial.Serial(port=port, baudrate=9600)
        time.sleep(2)
        self.camera_id= camera_id
        self._logger = logging.getLogger("Capper")
    def right(self):
        self._logger.info("Capper moving right")
        self.capper.write(b'R')
    def left(self):
        self._logger.info("Capper moving left")
        self.capper.write(b'L')
    def check_capping(self):
        cameracapper=CameraCapper(camera_id=self.camera_id)
        cameracapper.init_camera()
        cameracapper.start_streaming()
        capped=cameracapper.capped  
        time.sleep(5)
        del cameracapper
        return capped