
import sys
import os 

file_path = sys.path.insert(1, os.path.dirname(os.path.abspath(__file__))+'/..')

import serial
import time
from config.configuration import *
import logging

class Holder():
    def __init__(self,port=HOLDER_PORT):
        self.holder = serial.Serial(port=port, baudrate=9600)
        time.sleep(2)
        self._logger = logging.getLogger("PumpHolder")
    
    def holding_position(self):
        self._logger.info("Moving to holding/wash position")
        self.holder.write(b'1')

    def infusing_position(self):
        self._logger.info("Moving to dispensing position")
        self.holder.write(b'0')