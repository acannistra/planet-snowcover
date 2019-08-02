#!/bin/bash

# control script for Amazon Sagemaker train/serve container. 
# Tony Cannistra, 2019 

source activate pytorch_p36

if [ "$1" != "" ]; then
    echo "Initiating training with config $2."
    wget $2 -O "model-config.toml"
    cd robosat_pink/
    ./rsp train --config /opt/ml/input/data/config/*.toml /opt/ml/model/
fi


