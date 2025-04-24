##### Workflow Configuration Hardcodes for Dispense and Filtration Pumps #####


#Dictionary of the pump configuration of the tecan xcalibur in the liquid dispensing station of RiH
#Shows only ports hardcoded to have specific functions
#If changed by the user in software corresponding changes must be made in hardware
#Key - Liquid name
#Value - Port
DISPENSE_HARCDCODES = {
"Dispense": 1,
"Air": 2,
"Waste": 6,

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
