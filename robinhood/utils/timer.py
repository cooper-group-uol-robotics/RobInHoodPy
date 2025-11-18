import time
import threading
from datetime import datetime
import logging

class Timer():
    """
    This class can be used to generate long time pauses.

    :param display_timer: is an integer controls how long it takes to display updates, given in seconds, of the elapsed time
    """
    def __init__(self,display_updates_timer=1):
        self.seconds=0
        self.display_updates_timer=display_updates_timer
        self.display_time=False
        self.time_display_thread=threading.Thread(target=self.display_current_time)
        self._logger =logging.getLogger("Timer")


    def display_current_time(self):
        """
        Prints updates of the elapsed time since the timer was started. 
        """
        start_time=datetime.now()
        while self.display_time:
            current_time = datetime.now()
            elapsed_time= current_time - start_time
            hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
            minutes, seconds= divmod(remainder, 60)
            self._logger.info(f'Elapsed time: {int(hours)} h {int(minutes)} m {int(seconds)} s')
            time.sleep(self.display_updates_timer)
        return
    def set_timer(self,hours=0,min=0, sec=0):
        """
        Transforms the given hours, minutes and seconds into seconds.
        :param hours: integer
        :param min: integer
        :param sec: integer
        """
        self._logger.info(f'Setting timer to {hours} h {min} m {sec} s')
        self.seconds = 0
        if hours%24==0:
            self.seconds = self.seconds + hours*3600
        else:
            self.seconds = self.seconds + (hours%24)*3600
            self._logger.info(f"'Timer hour set to {self.seconds}'")
        if min%60 == 0:
            self.seconds = self.seconds +  min*60
        else:
            self.seconds = self.seconds + (min%60)*60
            self._logger.info(f"'Timer min set to {self.seconds}'")
        if sec%60 == 0:
            self.seconds = self.seconds +  sec
        else:
            self.seconds = self.seconds + sec%60
            self._logger.info(f"'Timer sec set to {self.seconds}'")
        #self.seconds=(hours%24)*3600+(min%60)*60+sec%60
        self._logger.info(f'Timer set to {self.seconds}')
        return
    def start_timer(self):
        """
        Starts a thread that allows displaying the elapsed time while producing a delay.
        """
        self.display_time=True
        try:
            self.time_display_thread.start()
        except:
            self.display_time=False
        time.sleep(self.seconds+1)
        self.display_time=False
        self.time_display_thread.join()
        self._logger.info(f'[INFO] Waiting finished....')
        return