import sys
import os 
from datetime import datetime
from rob_in_hood import RobInHood
import dye_workflow as mn

logname= datetime.now().strftime("%d_%m_%Y")
station=RobInHood(logname+"_log", sim=False,vel=0.05)



#station.filt_machine.wash_receiving_flask_pre(wash_volume=120000)

#input()

#station.filt_machine.filter_vial(12000,vacuum_time=3000)

# input()

# station.filt_machine.vacuum_off()

#station.filt_machine.recover_receiving_flask(30000)

station.filt_machine.wash_receiving_flask_post("Water(DI)", 30000)
