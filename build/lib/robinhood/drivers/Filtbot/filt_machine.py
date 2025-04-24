import sys
import os 
import logging

#sys.path.insert(1, os.path.dirname(os.path.abspath(__file__))+'/../..')

import serial
import time

from pylabware import XCalibur


class FiltMachine():
    def __init__(self, machine_port: str, pump_port: str,port_config: dict, machine_baud:int = 9600, switch_address = "1") -> None:
        self.machine_port = machine_port
        self.machine_baud = machine_baud
        self._stopped = False #checks if estop is on or off
        self._needle_dispense = False #keeps track of needle position
        self.port_config = port_config #dictionary of port identities for the tecanxcalibur
        self.pump_port = pump_port
        self.switch_address = switch_address
        

        # Logger object
        self._logger = logging.getLogger("RiH_Filtration_System")

    def ready_check(func):
        """Wrapper function checks for the state of the E stop and if the pump is ready to receive
          a new command before proceeding with the new function """

        def wrapper(self, *args, **kwargs):
            
            if self._stopped == True and func.__name__ == "estop_off": #Allows you to turn off the estop - allowing pressure back into the system
                self._logger.critical("E stop has been pressed - restarting the system")
                _pump_idle = self.pump.is_idle() 
                self._logger.info("Pump is idle running command")
                func(self, *args, **kwargs)

            elif self._stopped == True:
                self._logger.critical("E stop is on - restart system before sending further commands")    
            
            elif self._stopped == False:
                self._logger.info("E stop is off - checking pump is ready")
                _pump_idle = self.pump.is_idle() 
                self._logger.info("pump is idle running command")
                func(self, *args, **kwargs)
        
        return wrapper


   
    def initialise_filtmachine(self):
        
        self._logger.info("Initialising filtration system pump")
        #opening serial connection to the arduino
        self.ser = serial.Serial(self.machine_port, self.machine_baud)
        time.sleep(3)
        #Initialising the XCalibur pump
        self.pump = XCalibur('FILT_PUMP', 'serial', port = self.pump_port, switch_address = self.switch_address, address= "1", syringe_size= "5.0mL")
      
        self.pump.connect()
        self.pump.initialize_device(input_port=str(self.port_config["Waste"]), output_port=str(self.port_config["Waste"])) 
        self.pump.set_predefined_speed(velocity_code=13) # set slower speed as larger syringe

        self._logger.info("Initialising the filtration system arduino")
        
        
        




### Pump commands - controlling the filtration pump
    
    @ready_check
    def prime_system_solvent(self,  wash_solvent:str, volume:float = 2000):
        """Primes system solvent from valve_port into system waste"""
        """Current volume of reagent line 7 = 1.4 ml - dispenses 2 ml"""
        

        valve_port = self.port_config[wash_solvent]

        self._logger.info(f"Priming system solvent {wash_solvent} (port: {valve_port}) to system waste")
        self.pump.dispense(volume,source_port=valve_port,destination_port= self.port_config["Waste"] )

       

    @ready_check
    def recover_receiving_flask(self, vol:float):
        """recovers volume + 10 ml of filtrate from receiving flask to output needle"""

        self._logger.info(f"Recovering filtrate ({vol} + 10 mL) from receiving flask")
        if self._needle_dispense == True:
            true_vol  = vol + 10000
            self.pump.dispense(volume = true_vol, source_port= self.port_config["Receiving_Flask"], destination_port=self.port_config["Output_Needle"] )

        else: 
            self._logger.warning("Needle not positioned under receiving vial")

    
    
    
    @ready_check
    def wash_receiving_flask_pre(self, wash_volume: float =9000):
        """Before filtration a vial of the wash solvent is poured over a clean cartridge. This is to wet the filter,
        and wash the funnel and tubing ahead of the receiving flask. This removes that solvent cleaning the receiving flask before (pre) filtration."""
    
        self._logger.info(f"Recovering pre-filtration wash ({wash_volume} + 5 mL) from receiving flask")
        
        #aspirate vol ul + 5000 into system waste
        self.pump.dispense(volume= wash_volume + 5000, source_port= 
        self.port_config["Receiving_Flask"], destination_port= self.port_config["Waste"])

       
       
    
    
    @ready_check
    def wash_receiving_flask_post(self, wash_solvent:str, wash_volume:int):
        """cleans the receiving flask after (post) filtration and recovery of the filtrate liquid, uses solvent from wash_solvent_port specified
        """


        self._logger.info(f"Cleaning receiving flask with {2*wash_volume/1000} mL solvent:{wash_solvent}")
        #dispense vol ul system solvent into receiving flask 
        wash_port = self.port_config[wash_solvent]
        self.pump.dispense(volume=2*wash_volume, source_port=wash_port, destination_port= self.port_config["Receiving_Flask"])

        #aspirate vol ul + 10000 into system waste
        self.pump.dispense(volume= 2*wash_volume + 10000, source_port= self.port_config["Receiving_Flask"], destination_port= self.port_config["Waste"])


    @ready_check
    def wash_needle(self, wash_solvent:str):
        """Clean the needle after filtration. 
        Dispenses 4 mL of wash solvent followed by 4 mL of air to clean the line
        Needle tubing volume is approximately 0.630 ml"""

        self._logger.info(f"Washing output needle with 4 mL of solvent {wash_solvent}")
        port = self.port_config[wash_solvent]
        if self._needle_dispense == False: # Needle in the washing position
            #washing the needle with system solvent
            self.pump.dispense(volume = 4000, source_port= port, destination_port= self.port_config["Output_Needle"])
            #switching to empty port (at the moment 5) to push the last of the liquid out of the line
            self.pump.dispense(volume = 4000, source_port= self.port_config["Air"], destination_port=self.port_config["Output_Needle"])

        else:
            self._logger.error("Needle not positioned under washing position")

    
    @ready_check
    def purge_tubing_lines(self, volume: float = 5000):
        """Pushes volume (5 mL) of solvent from each line listed in the workflow configuration to purge them of sample"""
        
        if self._needle_dispense == False: #Needle in the washing position
            self._logger.info("Purging system ports")
            for key in self.port_config:
                if key == "Air":
                    pass # do not need to clean an empty port
                else:
                    self._logger.debug(f"Purging port {key}")
                    self.pump.dispense(volume, self.port_config["Air"], self.port_config[key])
        
        else:
            self._logger.error("Needle not positioned under washing position")



    @ready_check
    def flush(self,flush_volume:int, solvent:str):
        """Flush tubing, receiving vessel and needle repeatedly with solvent of choice """

        
        self.wash_position() 

        if self._needle_dispense == False:
            self._logger.info(f"Flushing system with {flush_volume/1000} mL of solvent {solvent} ")
            solvent_port = self.port_config[solvent]
            self.pump.dispense(volume=flush_volume, source_port=solvent_port, destination_port=self.port_config["Receiving_Flask"])
            self.pump.dispense(volume= flush_volume + 10000, source_port = self.port_config["Receiving_Flask"], destination_port=self.port_config["Output_Needle"])   
        
        else:
            self._logger.error("Needle not positioned under washing position")


### Machine Commands - Control of Pneumatics and Stepper Motors ###

    @ready_check
    def forward_pour(self) -> None:
        """Tilts the vial forward by approximately 130 degrees"""
        self._logger.info("Forward pouring")
        self.ser.write(b'0')
        time.sleep(15)

    @ready_check
    def backward_pour(self) -> None:
        """Tilts the vial backward by approximately 130 degrees"""
        self._logger.info("Backward pouring")
        self.ser.write(b'1')
        time.sleep(15)

    @ready_check
    def clamp(self) -> None: 
        """Actuates piston to clamp the vial"""
        self._logger.info("Clamping")
        self.ser.write(b'2')
        time.sleep(5)

    @ready_check
    def release(self) -> None:
        """Releases piston to release the vial"""
        self._logger.info("Releasing")
        self.ser.write(b'3')
        time.sleep(5)

    @ready_check
    def vacuum_on(self) -> None: 
        """Turns the vacuum on (indefinitely)"""
        self.pump.set_valve_position(self.port_config["Air"]) # switches valve so the pump not connected to receiving flask while vacuum pulled
        self._logger.info("Vacuum on")
        self.ser.write(b'4')
        time.sleep(5)
    
    @ready_check
    def vacuum_off(self) -> None:
        """Turns the vacuum off"""
        self._logger.info("Vacuum off")
        self.ser.write(b'5')
        time.sleep(5)

    @ready_check
    def dispense_position(self) -> None:
        """Moves the needle into the dispensing position"""
        self._logger.info("Moving needle to dispense position")
        self.ser.write(b'6')
        time.sleep(5)
        self._needle_dispense = True

    @ready_check
    def wash_position(self) -> None:
        """Moves the needle into the wash position"""
        self._logger.info("Moving needle to wash position")
        self.ser.write(b'7')
        time.sleep(5)
        self._needle_dispense = False

    @ready_check
    def estop_off(self) -> None:
        """Deactivates the estop - allowing pressure to the valves"""
        self._logger.info("De-activating emergency stop")
        self.ser.write(b'8')
        self._stopped = False
        

    @ready_check
    def  estop_on(self) -> None:
        """Activates the estop - venting the system"""
        self._logger.critical("Activating emergency stop")
        self.ser.write(b'9')
        self._stopped = True
        
 
    ### Combined Commands - higher level functions ### 

    def filter_setup(self, volume_filtered: int, wait_time: int, stepping: bool = False):
        """Tips a vial containing the wash solvent into an empty cartridge to clean/prep for filtration, 
        leaves vacuum on. Wait time is time in seconds between pouring and cleaning."""

        self._logger.info(f"Washing filter before start of filtering process with {volume_filtered/1000} mL")
        
        self.clamp()

        if stepping == True:
            input("Proceed?")

        self.forward_pour()
        
        if stepping == True:
            input("Proceed?")

        self.vacuum_on()
       
       
        if stepping == True:
            input("Proceed?")   

        self.backward_pour()

        if stepping == True:
            input("Proceed?")   

        #time.sleep(wait_time) 
        while True:
            self._logger.warning('Has the filtering finished?(y/n)')
            yn=input()
            if yn =='y' or yn =='Y':
                self._logger.info("Resuming workflow.")
                break
            elif yn == 'n' or yn == 'N':
                self._logger.info("Resuming filtering.")
            else:
                self._logger.info("Invalid option.")

     
        self.wash_receiving_flask_pre(wash_volume=volume_filtered)

        if stepping == True:
            input("Proceed?")

        self.release()

        if stepping == True:
            input("Proceed?")
    
    def filter_vial(self, volume_filtered: int, vacuum_time: int, stepping: bool = False):
        """Filters a sample.

        volume_filtered  = volume of sample in uL
        vacuum_time = filtering time in seconds

        """
        
        self._logger.info(f"Filtering {volume_filtered/1000} mL of solvent - vacuum will be on for {vacuum_time} s")

        self.clamp()

        if stepping == True:
            input("Proceed?")
        
        self.vacuum_on()

        self.forward_pour()

        #time.sleep(vacuum_time)

        while True:
            self._logger.warning('Has the filtering finished?(y/n)')
            yn=input()
            if yn =='y' or yn =='Y':
                self._logger.info("Resuming workflow.")
                break
            elif yn == 'n' or yn == 'N':
                self._logger.info("Resuming filtering.")
            else:
                self._logger.info("Invalid option.")
        


      
        self.vacuum_off()

        if stepping == True:
            input("Proceed?")

        self.backward_pour()

        if stepping == True:
            input("Proceed?")   

        self.dispense_position()

        if stepping == True:
            input("Proceed?")   

        self.recover_receiving_flask(vol = volume_filtered)

        if stepping == True:
            input("Proceed?")   

        self.wash_position()

        if stepping == True:
            input("Proceed?")   

        self.release()

        if stepping == True:
            input("Proceed?")  

    def clean(self, volume_filtered: float, wash_solvent: str, stepping: bool = False):

        """ cleans the receiving vial and the needles after filtering. 

        volume_filtered = volume of sample filtered in uL
        wash_solvent = dictionary entry of cleaning solvent to use in workflow_config
        
        
        """

        self._logger.info(f"Washing receiving flask with {volume_filtered/1000} mL of {wash_solvent}")

        self.wash_receiving_flask_post(wash_solvent=wash_solvent,wash_volume=volume_filtered)
        
        if stepping == True:
            input("Proceed?")  

        self.wash_needle(wash_solvent=wash_solvent)

        if stepping == True:
            input("Proceed?")







