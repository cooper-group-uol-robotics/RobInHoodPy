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

SAMPLE_PAIRS=("1 7" "2 8" "3 9" "4 10" "5 11" "6 12")


read_robot_state(){
    python $LOCAL_PATH/src/read_current_state.py
    python $LOCAL_PATH/src/read_current_state.py
    python $LOCAL_PATH/src/read_current_state.py
}

if [ ! -d "$DATASET_PATH" ]; then
    echo "[WARNING] Directory $DATASET_PATH does not exist."
    mkdir -p "$DATASET_PATH"
    mkdir -p "$OUTPUT_PATH"
    echo "[WARNING] Directory $DATASET_PATH has been created."
else 
    echo "[INFO] Directory $DATASET_PATH already exists."
fi

if [ ! -d "$OUTPUT_PATH" ]; then
    echo "[WARNING] Directory $OUTPUT_PATH does not exist."
    mkdir -p "$OUTPUT_PATH"
    echo "[WARNING] Directory $OUTPUT_PATH has been created."
else 
    echo "[INFO] Directory $OUTPUT_PATH already exists."
fi

echo "[INFO] Script running in $LOCAL_PATH"
echo "[INFO] Results will be saved in $DATASET_PATH"

# echo "[INFO] Filtering samples"
# for pair in "${SAMPLE_PAIRS[@]}"; do
#     echo "[INFO] Reading robot state:"
#     read_robot_state 
#     python $LOCAL_PATH/dye_workflow.py "filter_samples" $pair
# done

echo "[INFO] Reading robot state:"
read_robot_state

echo "[INFO] Photographing samples"
python $LOCAL_PATH/dye_workflow.py "photograph_samples" $1 $DATASET_PATH

echo "[INFO] Colorimetry"
python $LOCAL_PATH/src/colorimetry.py $1 $LOCAL_PATH"/" 

echo "[INFO] Reading robot state:"
read_robot_state

echo "[INFO] Cleaning and Setting Down workflow"
python $LOCAL_PATH/dye_workflow.py "cleaning_filtering_pump" 

echo "[INFO] Process complete."