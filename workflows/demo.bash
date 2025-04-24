###############################################################
# Prepares 6 samples of a given solid and one different dye   # 
# each [dye1, dye2, dye3, dye4, dye5, dye6]                   #
###############################################################

#!/bin/bash
set -e

LOCAL_PATH=$(pwd)
TEMP_PATH="$LOCAL_PATH/TEMP"
DATASET_PATH="$TEMP_PATH/$1/imgs"
LOGNAME="$2"
OUTPUT_PATH="$TEMP_PATH/$1/ROI_output"

SAMPLE_PAIRS=("1 7")


read_robot_state(){
    python $LOCAL_PATH/src/read_current_state.py
    python $LOCAL_PATH/src/read_current_state.py
    python $LOCAL_PATH/src/read_current_state.py
}


echo "[INFO] Reading robot state:"
read_robot_state 

echo "[INFO] Preparing samples in progress."
python $LOCAL_PATH/main.py "demo"

echo "[INFO] Process complete."