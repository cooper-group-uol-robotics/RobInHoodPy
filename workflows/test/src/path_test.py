
from datetime import datetime 
import os
import sys
from robinhood import RobInHood


logname= datetime.now().strftime("%d_%m_%Y")
station=RobInHood(logname+"_log", sim=False,vel=0.05)


print(station.sample_dict)