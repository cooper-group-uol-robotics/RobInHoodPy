
####################TODO remove when making this a pip package
import sys
import os 
file_path = sys.path.insert(1, os.path.dirname(os.path.abspath(__file__))+'/..')
####################

import pandas
import os
import logging
import sys
import datetime


from robinhood.config.workflow_config import FILTRATION_HARDCODES, DISPENSE_HARDCODES, PUMP_PORT_ASSIGNMENTS

class Workflow_Helper:
    
    def __init__(self, config_path: str ,  data_path:str, config_type:str = "csv", sample_type: str = "csv" ) -> None:
        """
        Worfklow helper - allows easy configuration of the sample and workflow dictionaries from csv files.
        Sets the data directory in which results will be placed. 

        For workflow file specificatiself.config_pathons see documentation.

        inputs:
            config_path = path to the configuration files(s)
            data_path = path where data files will be saved (creates directory if one does not exist)
            config_type = specified filetype to look for workflow configuration (.csv or .xlsx)
            sample_type = specified filetype to look for for samples (.csv or .xlsx)
        
        """
        
        #starting logger
        self._logger = logging.getLogger("Workflow_Config_Helper")
        self.config_path= config_path
        self.data_path  =  data_path

        if not os.path.exists(self.data_path):
            self._logger.info("No data directory found, creating it")
            os.mkdir(self.data_path)

        else:
            self._logger.debug(f"Data folder found: {self.data_path}")

        self.config_path =  config_path

        try:
            os.path.isdir(self.config_path)
            self._logger.debug(f"Config folder found: {self.config_path}")
        
        except FileNotFoundError: 
            self._logger.error(f"No config directory found at {self.config_path}")
            os.mkdir(self.config_path)
        

        self.config_type = config_type
        self.sample_type = sample_type


        self.dispense_hardcodes = DISPENSE_HARDCODES
        self.filtration_hardcodes = FILTRATION_HARDCODES
     


    def workflow_setup(self) -> dict:
        """Combination method of all needed loading and validating workflow methods in the workflow helper class run in the correct order.
        
        outputs:
        dispense, quantos and filtration dictionaries with the metadata removed
        sample dictionary
        
        
        """


        if self.config_type == "csv":
            self._logger.debug("Loading workflow configuration dictionaries from csv")
            dispense_dict, quantos_dict, filt_dict = self.make_config_csv()
 
        elif self.config_type == "xlsx":
            self._logger.debug("Loading workflow configuration dictionaries from xlsx")
            dispense_dict, quantos_dict, filt_dict = self.make_config_excel()

        else:
            self._logger.error(f"Unsupported file type for workflow configuration {self.config_type}")

        if self.sample_type == "csv":
            self._logger.debug("Loading sample dictionaries from csv")
            sample_dict = self.make_samples_csv()

        elif self.sample_type == "xlsx":
            self._logger.debug("Loading sample dictionaries from csv")
            sample_dict = self.make_samples_excel()

        else: 
            self._logger.error(f"Unsupported file type for sample file {self.sample_type}")
         
        self.validate_samples(samples_dict=sample_dict, dispense_dict=dispense_dict, quantos_dict=quantos_dict)
        
        self.validate_workflow(dispense_config=dispense_dict,filt_config=filt_dict)

        self.log_workflow_metadata(dispense=dispense_dict, quantos=quantos_dict, filtration=filt_dict)

        return dispense_dict["port"],dispense_dict["meta"], quantos_dict["position"], filt_dict["port"], sample_dict

   
    def make_config_excel(self, config_name: str = "config.xlsx") -> dict:
        """Creates python dictionaries for port configurations for the dispense pump and filtration pumps. 
        Also creates a python dictionary for the quantos cartridge positions.
        
        inputs: config_name - name of config file (.xlsx)
        
        outputs: seperate dictionaries for the dispense, filtration and quantos configurations
        """
        
        try:
            dispense_df = pandas.read_excel(io=self.config_path + "/" + config_name, usecols = ["ID","port", "meta"], sheet_name = "dispense")
            dispense_dict = dispense_df.fillna(value = "None").set_index("ID").to_dict()
        
        except Exception as e:
           self._logger.error(f"An error occured in the dispense config {e}")
           exit()

        try:
            quantos_df = pandas.read_excel(io=self.config_path + "/" + config_name, usecols = ["ID","position", "meta"], sheet_name = "quantos")
            quantos_dict = quantos_df.fillna(value = "None").set_index("ID").to_dict()
        
        except Exception as e:
           self._logger.error(f"An error occured in the quantos config {e}")
           exit()

        try:
            filt_df = pandas.read_excel(io=self.config_path + "/" + config_name, usecols = ["ID","port", "meta"], sheet_name = "filt")
            filt_dict = filt_df.fillna(value = "None").set_index("ID").to_dict()
                        
        except Exception as e:
           self._logger.error(f"An error occured in the filtering config {e}")
           exit()

        return dispense_dict, quantos_dict, filt_dict

    
    def make_config_csv(self) -> dict:
        """Creates python dictionaries for port configurations for the dispense pump and filtration pumps. 
        Also creates a python dictionary for the quantos cartridge positions.
        
        This script will look in the the specified config path for three csv files - dispense, quantos, and filt and
        use them to create the relevant dictionaries. 
        
        outputs: seperate dictionaries for the dispense, filtration and quantos configurations
        """

        try:
            dispense_df = pandas.read_csv(self.config_path + "/dispense.csv", usecols = ["ID","port", "meta"])
            dispense_dict = dispense_df.fillna(value = "None").set_index("ID").to_dict()
         

           
        
        except Exception as e:
           self._logger.error(f"An error occured in the dispense config {e}")
           exit()

        try:
            quantos_df = pandas.read_csv(self.config_path + "/quantos.csv", usecols = ["ID","position", "meta"])
            quantos_dict = quantos_df.fillna(value = "None").set_index("ID").to_dict()
            
        
        except Exception as e:
           self._logger.error(f"An error occured in the quantos config {e}")
           exit()

        try:
            filt_df = pandas.read_csv(self.config_path + "/filt.csv", usecols = ["ID","port", "meta"])
            filt_dict = filt_df.fillna(value = "None").set_index("ID").to_dict()
            
                        
        except Exception as e:
           self._logger.error(f"An error occured in the filtering config {e}")
           exit()




        return dispense_dict, quantos_dict, filt_dict

    def make_samples_excel(self, samples_name:str = "samples.xlsx") -> dict:
        """Creates a python dictionary of samples to be prepared by RiH.
        
        input: sample_name - name of the sample dictionary where the desired liquids and solids are stored
        output: dictionary of samples to be processed
        """
        try:
            samples_df = pandas.read_excel(io=self.config_path + "/" + samples_name, usecols = ["vial","liquid", "volume (ml)", "solid", "mass (mg)", "meta"])
            samples_dict = samples_df.fillna(value = "None").to_dict('index')
            
            for entry in samples_dict:
                samples_dict[entry]["liquid"] = str(samples_dict[entry]["liquid"]).split(":")
                samples_dict[entry]["volume (ml)"] = str(samples_dict[entry]["volume (ml)"]).split(":")
                samples_dict[entry]["solid"] = str(samples_dict[entry]["solid"]).split(":")
                samples_dict[entry]["mass (mg)"] = str(samples_dict[entry]["mass (mg)"]).split(":")
        
            

        except Exception as e:
            self._logger.error(f"An error occured in the samples list {e}")
            exit()


        return samples_dict 
    

    def make_samples_csv(self, samples_name: str = "samples.csv") -> dict:
        """Creates a python dictionary of samples to be prepared by RiH.
        
        input: sample_name - name of the sample dictionary where the desired liquids and solids are stored
        output: dictionary of samples to be processed
        """
        try:
            samples_df = pandas.read_csv(self.config_path + "/" + samples_name, usecols = ["vial","liquid", "volume (ml)", "solid", "mass (mg)", "meta"])
            samples_dict = samples_df.fillna(value = "None").to_dict('index')

            for entry in samples_dict:
                samples_dict[entry]["liquid"] = str(samples_dict[entry]["liquid"]).split(":")
                samples_dict[entry]["volume (ml)"] = str(samples_dict[entry]["volume (ml)"]).split(":")
                samples_dict[entry]["solid"] = str(samples_dict[entry]["solid"]).split(":")
                samples_dict[entry]["mass (mg)"] = str(samples_dict[entry]["mass (mg)"]).split(":")
                samples_dict[entry]["meta"] = str(samples_dict[entry]["meta"]).split(":") 





        except Exception as e:
            self._logger.error(f"An error occured in the samples list {e}")
            exit()

        return samples_dict 
    
    
    def validate_workflow(self, dispense_config: dict, filt_config: dict):
        """
        Checks that the workflow configuration dictionaries input by the user are compliant against hardcoded settings for the pumps 
        in the liquid dispensing and filtration stations. These settings are set in the configuration files for the RiH package. 
        Exits if errors are found. 

        inputs: dispense_config and filt_config dictionaries to be checked. 
        
        """
        
        _error_flag = False # there must be a better way to do this


        for key in self.dispense_hardcodes:
            try:
               
                assert self.dispense_hardcodes[key] == dispense_config["port"][key], "Value error"
                self._logger.debug(f"{key} matches config and is on port {self.dispense_hardcodes[key]}")
            
            except AssertionError as ve:
                self._logger.error(f"{ve}: {key} must be set to port: {self.dispense_hardcodes[key]}")
                _error_flag = True

            except KeyError as ke:
                self._logger.error(f" KeyError: {ke} No {key} port set in workflow - set to port: {self.dispense_hardcodes[key]}")
                _error_flag = True
                
        for key in self.filtration_hardcodes:
            try:
                assert self.filtration_hardcodes[key] == filt_config["port"][key], "Value error"
                self._logger.debug(f"{key} matches config and is on port {self.filtration_hardcodes[key]}")
            
            except AssertionError as ve:
                self._logger.error(f"{ve}: {key} must be set to port {self.filtration_hardcodes[key]}")
                _error_flag = True
                
            except KeyError as ke:
                self._logger.error(f"KeyError: {ke} No {key} port set in workflow - set to port: {self.filtration_hardcodes[key]}")
                _error_flag = True
                
     

        if _error_flag:
            self._logger.error("One or more errors found in configuration files")
            exit()

        else:
            self._logger.info("No errors in workflow detected")
         
               


    def validate_samples(self,samples_dict: dict, dispense_dict:dict, quantos_dict:dict):
        """
        Checks that the solids and liquids requested by the user in the samples_dict are present in the workflow.
        Warning: Case sensitive for liquid and solid names 
        Exits if errors are found

        inputs: samples_dict, dispense_config and filt_config dictionaries to be checked. 
        
        """

        liquid_errors = []
        solid_errors = []

        for id in samples_dict:

            for liquid in samples_dict[id]["liquid"]:
              
                if liquid not in dispense_dict["port"].keys() and samples_dict[id]["liquid"] != "None":    
                    self._logger.error(f"Liquid requested {samples_dict[id]['liquid']} is not connected to the pump")
                    self._logger.error(f"Liquids available: {dispense_dict['port'].keys()}")
                    liquid_errors.append(samples_dict[id]['liquid'])
                
            for solid in samples_dict[id]["solid"]:
            
                if solid not in quantos_dict["position"].keys() and samples_dict[id]["solid"] != "None":
                    self._logger.error(f"Solid requested {samples_dict[id]['solid']} is not in a Loaded Quantos Cartridge")
                    solid_errors.append(samples_dict[id]["solid"])

        try:
            
            assert  len(liquid_errors) == 0 and len(solid_errors) == 0, "Errors found between chemicals requested and those in workflow configuration"

        except AssertionError as ae:
            self._logger.error(f"{ae} - Liquid Errors: {liquid_errors} Solid Errors: {solid_errors}")
            exit()

        else:
            self._logger.info("All solids and liquids requested in sample list are in the workflow")


    def log_workflow_metadata(self, dispense: dict, quantos: dict, filtration: dict):

        self._logger.info("Writing setup dictionaries")
        self._logger.info("Dispense Dictionary:")
        self._logger.info(dispense)
        self._logger.info("Quantos Dictionary:")
        self._logger.info(quantos)
        self._logger.info("Filtration Dictionary")
        self._logger.info(filtration)



if __name__ == "__main__":
   test_handler = logging.StreamHandler(sys.stdout)
   logging.basicConfig(format= "%(asctime)s - %(name)s - %(levelname)s - %(message)s", level = "DEBUG", handlers = [test_handler])
   
   config_path = "C:\\Users\\Louis_Work\\documents\\pythonscripts\\Robinhood\\RobInHoodPy\\robinhood\\setup"
   data_path = "C:\\Users\\Louis_Work\\documents\\pythonscripts\\Robinhood\\RobInHoodPy\\data"


   test = Workflow_Helper(config_path=config_path, data_path=data_path, config_type="csv", sample_type="csv")
   test.workflow_setup()
   
   print("done")

