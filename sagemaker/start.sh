#!/bin/bash

# control script for Amazon Sagemaker train/serve container.,
#
# .toml configuration files speficied in training job creation
# are supplied by SageMaker and placed in /opt/ml/input/data/config.
# ("config" is channel name.)
#
# Model outputs saved in /opt/ml/model are uploaded to S3 under
# prefix specified in training job creation.
#
# Tony Cannistra, 2019

source activate pytorch_p36

if [ "$1" == "train" ]; then
    echo "Initiating training with config $2."
    cd robosat_pink/
    ./rsp train --config /opt/ml/input/data/config/*.toml /opt/ml/model/
elif [ "$1" == "lab"]; then 
    echo "starting jupyterlab (8888)"
    jupyter lab --ip=0.0.0.0
fi
