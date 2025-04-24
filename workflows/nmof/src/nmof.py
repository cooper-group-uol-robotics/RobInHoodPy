import sys
import os 
from datetime import datetime
from rob_in_hood import RobInHood
import dye_workflow as mn

#This script makes NMOFS see main for a more detailed description of functions
logname= datetime.now().strftime("%d_%m_%Y")
station=RobInHood(logname+"_log", sim=False,vel=0.05)
#mn.prime_lines(station = station)
mn.prepare_nmof_samples(station = station)
