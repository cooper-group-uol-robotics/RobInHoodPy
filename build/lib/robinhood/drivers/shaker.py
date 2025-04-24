import serial
import time
from config.configuration import *
import logging

class Shaker():
    def __init__(self,port=SHAKER_PORT):
        self.shaker = serial.Serial(port=port, baudrate=9600)
        time.sleep(2)
        self._logger = logging.getLogger("Shaker")


    def on(self):
        self._logger.info("Shaker on")
        self.shaker.write(b'1')
    def off(self):
        self._logger.info("Shaker off")
        self.shaker.write(b'0')