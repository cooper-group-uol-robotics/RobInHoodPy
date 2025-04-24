from config.configuration import *
import cv2
import threading
import time
import random
import os
import numpy as np
import pyrealsense2 as rs
import math
import logging

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

        self._logger = logging.getLogger("Camera")

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
                self._logger.info(f'Camera ID = {self.camera_id} connected.')
                return True
        except:
            self._logger.info(f'Camera ID = {self.camera_id} connected.')
            return False
    
    def stop_streaming(self):
        """
        Stops the thread running the video streaming.
        """
        self._logger.info("Camera stream stopped")
        
        self.stream=False
    
    
    def start_streaming(self):
        """
        Starts the thread that runs the video streaming.
        """
        self._logger.info("Camera stream started")
        self.stream=True
        self.streaming_thread.start()

    def camera_stream(self):
        """
        Streams the images from the camera.
        """
        while self.stream:
            _,self.img= self.video.read()
            if not _:
                self._logger.error("No frame available.")
                break
            cv2.imshow("Gripper's camera view",self.img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()
        self.video.release()

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
                x,y,w,h= 60, 250, 325, 175
                filename=name
                self._logger.info(path+name)
                cv2.imwrite(path+name+".jpg", self.img[x:x+w,y:y+h])
            else:
                filename=f'{name}_{random.randint(0,100)}{random.randint(0,100)}{random.randint(0,100)}.jpg'
                cv2.imwrite(path+filename, self.img)
                self._logger.info(f'Image {filename} saved.')
        except:
            self._logger.error("Could not save picture.")
        return

    def save_picture_series(self, file_name, series_folder, path = IMGS_PATH):
        
        series_path = path + series_folder

        if os.path.exists(series_path):
            pass
            #print(f"Series directory {series_path} already exists - overwriting it")

        else:
            os.mkdir(series_path)

        try:
            
            cv2.imwrite(series_path+file_name, self.img)

            self._logger.info(f'Image {file_name} saved.')
        except:
            self._logger.error("Could not save picture.")
        return
    
    def test_save(self, file_name, series_folder, path = IMGS_PATH):
        
        series_path = path + series_folder

        if os.path.exists(series_path):
            pass
            #print(f"Series directory {series_path} already exists - overwriting it")

        else:
            os.mkdir(series_path)

        

            
        cv2.imwrite(series_path+file_name, self.img)

        self._logger.info(f'Image {file_name} saved.')

        return

class CameraCapper():
    """
    This class connects with a camera and streams video while running in a thread.
    :param camera_id: integer
    """
    def __init__(self,camera_id=0):
        self.camera_id=camera_id
        self.img=None
        self.video=None
        self.stream=True
        self.capped=False
        #self.streaming_thread=threading.Thread(target=self.camera_stream)
        #self.lock=threading.Lock()
        self._logger = logging.getLogger("Capper Camera")

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
                self._logger.info(f'Camera ID = {self.camera_id} connected.')
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
        x, y, w, h = 280, 200, 100, 170
        for _ in range(100):
            _,self.img= self.video.read()
            if not _:
                self._logger.error("No frame available.")
                break
            color_image_rgb=np.asanyarray(self.img)[x:x+w, y:y+h]
            #(hMin = 65 , sMin = 42, vMin = 174), (hMax = 179 , sMax = 255, vMax = 255)
            #color_image_rgb=np.asanyarray(color_image)
            hsv = cv2.cvtColor(color_image_rgb, cv2.COLOR_BGR2HSV)
            lower = np.array([65,42,174])
            upper = np.array([179,255,255])
            mask = cv2.inRange(hsv, lower, upper)
            color_image_rgb= cv2.bitwise_and(color_image_rgb, color_image_rgb, mask = mask)
            output = cv2.bitwise_and(color_image_rgb,color_image_rgb, mask= mask)
            gray = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cnts = cnts[0] if len(cnts) == 2 else cnts[1]
            threadsArea=0
            for cnt in cnts:
                threadsArea+=cv2.contourArea(cnt)
            if threadsArea>10:
                cv2.putText(self.img, "Not Capped!", (y-5, x-15),cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                cv2.rectangle(self.img, (y,x), (y+h,x+w), (0,0,255), 2)
                self.capped=False
            else:
                cv2.putText(self.img, "Capped!", (y+25, x-15),cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)
                cv2.rectangle(self.img, (y,x), (y+h,x+w), (0,255,0), 2)
                self.capped=True
            cv2.imshow("Capper's camera view",self.img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            time.sleep(0.1)
        self.video.release()
        del self.video
        cv2.destroyAllWindows()
        return
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
                x,y,w,h= 60, 250, 325, 175
                filename=name
                self._logger.info(path+name)
                cv2.imwrite(path+name+".jpg", self.img[x:x+w,y:y+h])
            else:
                filename=f'{name}_{random.randint(0,100)}{random.randint(0,100)}{random.randint(0,100)}.jpg'
                cv2.imwrite(path+filename, self.img)
                self._logger.info(f'Image {filename} saved.')

        except:
            self._logger.error("Could not save picture.")

        return

    def save_picture_series(self, file_name, series_folder, path = IMGS_PATH):
        
        series_path = path + series_folder

        if os.path.exists(series_path):
            pass
            #print(f"Series directory {series_path} already exists - overwriting it")

        else:
            os.mkdir(series_path)

        try:
            
            cv2.imwrite(series_path+file_name, self.img)

            self._logger.info(f'Image {file_name} saved.')

        except:
            self._logger.error("Could not save picture.")

        return
    
    def test_save(self, file_name, series_folder, path = IMGS_PATH):
        
        series_path = path + series_folder

        if os.path.exists(series_path):
            pass
            #print(f"Series directory {series_path} already exists - overwriting it")

        else:
            os.mkdir(series_path)

        

            
        cv2.imwrite(series_path+file_name, self.img)

        self._logger.info(f'Image {file_name} saved.')

        return   

class RSCamera:
    def __init__(self,dataset_name=""):
        # Configure depth and color streams
        self.dataset_name=dataset_name
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        self._logger = logging.getLogger("RSCamera")

        try:
            pipeline_profile = self.config.resolve(pipeline_wrapper)
            self.device = pipeline_profile.get_device()
            self.device_product_line = str(self.device.get_info(rs.camera_info.product_line))
            self.intr=0
            self.camera_checkup(False)
            self.number=0
            self.stream=True
            self.streaming_thread = threading.Thread(target=self.realsense)
            self.streaming_thread.start()
            self.color_image=None
        except:
            self._logger.error("No RealSense Connected.")
    
    def camera_checkup(self,found_rgb):
        for s in self.device.sensors:
            if s.get_info(rs.camera_info.name) == 'RGB Camera':
                found_rgb = True
                break
        if not found_rgb:
            self._logger.error("This requires Depth camera with Color sensor")
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

        if self.device_product_line == 'L500':
            self.config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
        else:
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

        # Start streaming
        cfg=self.pipeline.start(self.config)
        profile = cfg.get_stream(rs.stream.depth)

    def realsense(self):
        align_to = rs.stream.color
        align = rs.align(align_to)
        while self.stream:
                frames = self.pipeline.wait_for_frames(timeout_ms=10000)
                if not frames:
                    continue
                aligned_frames = align.process(frames)
                depth_frame = aligned_frames.get_depth_frame()
                color_frame = aligned_frames.get_color_frame()
                if not depth_frame or not color_frame:
                    continue
                self.intr = rs.video_stream_profile(depth_frame.profile).get_intrinsics()
                depth_image = np.asanyarray(depth_frame.get_data())
                self.color_image = np.asanyarray(color_frame.get_data())
                try:
                    #self.depth_img=np.asanyarray(depth_frame.get_data())
                    cv2.imshow('RealSense Stream', self.color_image)
                except:
                    continue
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        self.pipeline.stop()
        cv2.destroyAllWindows()
    def save(self,obj,path):
        if self.color_image is not None:
            self.number+=1
            filename=path+obj+str(self.number)+".jpg"
            cv2.imwrite(filename, self.color_image)
        return self.number
    def save_picture(self,name,path=IMGS_PATH,crop=False, x =0,y =0, w =10, h =10):
        """
        Saves a picture from the camera with a given name and arandomly generated id.
        :param name: name of the picture
        :type string: 
        :param path: path where the image is going to be saved
        :type string:
        """
        try:
            if crop:
                filename=name
                self._logger.info(path+name)
                cv2.imwrite(path+name+".jpg", self.color_image[x:x+w,y:y+h])
            else:
                filename=f'{name}_{random.randint(0,100)}{random.randint(0,100)}{random.randint(0,100)}.jpg'
                cv2.imwrite(path+filename, self.color_image)
                self._logger.info(f'Image {filename} saved.')
        except:
            self._logger.error("Could not save picture.")
        return


    


        