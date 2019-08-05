#!/bin/bash

# control script for Amazon Sagemaker train/serve container. 
# Tony Cannistra, 2019 

source activate pytorch_p36

if [ "$1" == "train" ]; then
    echo "Initiating training with config $2."
    ls /opt/ml/input/data/config/*.toml
    cd robosat_pink/
    ./rsp train --config /opt/ml/input/data/config/*.toml /opt/ml/model/
elif [ "$1" == "lab" ]; then 
    echo "Starting Jupyterlab...(port:8888)"
    jupyter lab --allow-root --ip=0.0.0.0 
fi


