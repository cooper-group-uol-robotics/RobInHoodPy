
import sys
import os 

main_path = os.path.dirname(os.path.abspath(__file__))+'/..'
sys.path.insert(1, main_path)

import serial
import time
from ..config.configuration import *
import logging
import cv2
import threading
import numpy as np

class LightBox():
    def __init__(self,port=LIGHTBOX_PORT,camera_id=2):
        self.holder = serial.Serial(port=port, baudrate=9600)
        self.camera_id=camera_id
        time.sleep(2)
        self._logger = logging.getLogger("Lightbox.")
    def opening_lightbox(self):
        self._logger.info("Opening the lightbox.")
        self.holder.write(b'1')
        time.sleep(15)
    def closing_lightbox(self):
        self._logger.info("Closing the lightbox.")
        self.holder.write(b'0')
        time.sleep(15)
    def light_on(self):
        self._logger.info("Switching light on.")
        self.holder.write(b'3')
        time.sleep(1)
    def light_off(self):
        self._logger.info("Switching light off.")
        self.holder.write(b'4')
        time.sleep(1)
    def stirr_on(self):
        self._logger.info("Stirring on.")
        self.holder.write(b'6')
        time.sleep(1)
    def stirr_off(self):
        self._logger.info("Stirring off.")
        self.holder.write(b'5')
        time.sleep(1)
    def take_picture(self,dye_name="",solid_name="",path=main_path+"/data/imgs/experiment1/"):
        lightbox_camera=LightboxCamera(camera_id=self.camera_id)
        lightbox_camera.init_camera()
        lightbox_camera.start_streaming()
        lightbox_camera.save_picture(name=solid_name+"_"+dye_name, path=path)
        time.sleep(1)
        del lightbox_camera

class LightboxCamera():
    """
    This class connects with a camera and streams video while running in a thread.
    :param camera_id: integer
    """
    def __init__(self,camera_id=0):
        self.camera_id=camera_id
        self.img=None
        self.video=None
        self.stream=True
        self._logger = logging.getLogger("Lightbox Camera")

    def init_camera(self):
        """
        Connects to a camera
        :returns: Returns True when the connection was succesful, False otherwise.
        :type: bool
        """
        try:
            self.video=cv2.VideoCapture(self.camera_id)
            time.sleep(2)
            if not self.video.isOpened():
                self._logger.error("Camera not available.")
                return False
            else:    
                self._logger.info(f'Camera with ID = {self.camera_id} connected.')
                return True
        except:
            self._logger.info(f'Camera ID = {self.camera_id} connected.')
            return False

    def start_streaming(self):
        """
        Starts the thread that runs the video streaming.
        """
        
        self._logger.info("Starting camera stream")
        self.stream=True
        self.camera_stream()

    
    def camera_stream(self):
        """
        Streams the images from the camera.
        """
        #x, y, w, h = 280, 200, 100, 170
        for _ in range(50):
            _,self.img= self.video.read()
            if not _:
                self._logger.error("No frame available.")
                break
            #color_image_rgb=np.asanyarray(self.img)[x:x+w, y:y+h]
            cv2.imshow("Lightbox's camera view",self.img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()
        print('releasing camera')
        self.video.release()
        del self.video
        print('Camera object deleted')
    def save_picture(self,name,path=IMGS_PATH,crop=False):
        """
        Saves a picture from the camera with a given name and arandomly generated id.
        :param name: name of the picture
        :type string: 
        :param path: path where the image is going to be saved
        :type string:
        """
        try:
            if crop:
                x, y, w, h = 280, 200, 100, 170
                filename=name
                self._logger.info(path+name)
                cv2.imwrite(path+name+".jpg", self.img[x:x+w,y:y+h])
            else:
                filename=name
                rotated_img=cv2.rotate(self.img, cv2.ROTATE_180)
                cv2.imwrite(path+"/"+name+".jpg", rotated_img)
                #print(path+filename)
                self._logger.info(f'Image {filename} saved.')
        except:
            self._logger.error("Could not save picture.")
        return
