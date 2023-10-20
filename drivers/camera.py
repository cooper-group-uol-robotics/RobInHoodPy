from conf.configuration import *
import cv2
import threading
import time
import random

class Camera():
    """
    This class connects with a camera and streams video while running in a thread.
    :param camera_id: integer
    """
    def __init__(self,camera_id=0):
        self.camera_id=camera_id
        self.img=None
        self.video=None
        self.stream=True
        self.streaming_thread=threading.Thread(target=self.camera_stream)
    def init_camera(self):
        """
        Connects to a camera
        :returns: Returns True when the connection was succesful, False otherwise.
        :type: bool
        """
        try:
            self.video=cv2.VideoCapture(self.camera_id)
            if not self.video.isOpened():
                print("[ERROR] Camera not available.")
                return False
            else:    
                print(f'[INFO] Camera ID = {self.camera_id} connected.')
                return True
        except:
            print(f'[INFO] Camera ID = {self.camera_id} connected.')
            return False
    def stop_streaming(self):
        """
        Stops the thread running the video streaming.
        """
        self.stream=False
    def start_streaming(self):
        """
        Starts the thread that runs the video streaming.
        """
        self.stream=True
        self.streaming_thread.start()
    def camera_stream(self):
        """
        Streams the images from the camera.
        """
        while self.stream:
            _,self.img= self.video.read()
            if not _:
                print("[ERROR] Not frame available.")
                break
            cv2.imshow("Gripper's camera view",self.img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()
        self.video.release()
    def save_picture(self,name,path=IMGS_PATH):
        """
        Saves a picture from the camera with a given name and arandomly generated id.
        :param name: name of the picture
        :type string: 
        :param path: path where the image is going to be saved
        :type string:
        """
        try:
            filename=f'{name}_{random.randint(0,100)}{random.randint(0,100)}{random.randint(0,100)}.jpg'
            cv2.imwrite(path+filename, self.img)
            print(f'[INFO] Image {filename} saved.')
        except:
            print("[ERROR] Could not save picture.")
        return