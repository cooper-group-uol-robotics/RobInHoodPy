from rob_in_hood import RobInHood
from config.configuration import *
import math
import time
import logging



PORT_DICT = {

1 : "Dispense",
2: "Air",
3: "",
4: "",
5: "DYE_1",
6: "Waste",
7: "DYE_2",
8: "DYE_3",
9: "DYE_4",
10: "",
11: "DYE_5",
12:"DYE_6"

}


def prime_reagent_lines(station):
    #station=RobInHood(inst_logger = 'priming_test', sim=False,vel=0.05)
    station.pump_prime_reagent_tubing(5)
    station.pump_prime_reagent_tubing(7)
    station.pump_prime_reagent_tubing(8)
    station.pump_prime_reagent_tubing(9)
    station.pump_prime_reagent_tubing(11)
    station.pump_prime_reagent_tubing(12)


if __name__ == "__main__":

    station=RobInHood(inst_logger = 'reagent_priming_test', sim=False,vel=0.05)
    prime_reagent_lines(station)
    