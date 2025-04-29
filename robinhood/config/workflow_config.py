##### Workflow Configuration Hardcodes for Dispense and Filtration Pumps #####



PUMP_PORT_ASSIGNMENTS = {

"Dispense_1":
{"name": "Tecan", 
 "ports":[0,1,2,3,4,5,6,7,8,9,10,11,12]
}
,
"Dispense_2":
{"name": "Tricont", 
 "ports":[13,14,15,16,17,18]
}
}





#Dictionary of the pump configuration of the tecan xcalibur in the liquid dispensing station of RiH
#Shows only ports hardcoded to have specific functions
#If changed by the user in software corresponding changes must be made in hardware
#Key - Liquid name
#Value - Port
DISPENSE_HARDCODES = {
"Dispense": 1,
"Air": 2,
"Waste": 6,
"Dispense_2": 13,
"Air_2": 15,
"Waste_2": 18

}   


#Dictionary of the pump configuration of the tecan xcalibur in the filtration station of RiH
#Shows only ports hardcoded to have specific functions
#If changed by the user in software corresponding changes must be made in hardware
#Key - Liquid name
#Value - Port


FILTRATION_HARDCODES={
"Receiving_Flask": 1,
"Priming_Waste": 2,
"Waste": 3,
"Output_Needle": 4,
"Air": 5
}


