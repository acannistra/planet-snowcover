#!/bin/bash

set -e

# OVERVIEW
# This script installs a custom, persistent installation of conda on the Notebook Instance's EBS volume, and ensures that these custom environments
# are available as kernels in Jupyter.
#
# The on-create script downloads and installs a custom conda installation to the EBS volume via Miniconda. Any relevant packages can be installed here
#   1. ipykernel is installed to
#   2. Ensure the Notebook Instance has internet connectivity to download the Miniconda installer
#
# For another example, see https://docs.aws.amazon.com/sagemaker/latest/dg/nbi-add-external.html#nbi-isolated-environment

sudo -u ec2-user -i <<'EOF'
unset SUDO_UID

# Install a separate conda installation via Miniconda
WORKING_DIR=/home/ec2-user/SageMaker/custom-miniconda
mkdir -p "$WORKING_DIR"
wget https://repo.anaconda.com/miniconda/Miniconda3-4.6.14-Linux-x86_64.sh -O "$WORKING_DIR/miniconda.sh"
bash "$WORKING_DIR/miniconda.sh" -b -u -p "$WORKING_DIR/miniconda"
rm -rf "$WORKING_DIR/miniconda.sh"


# Create a custom conda environment
source "$WORKING_DIR/miniconda/bin/activate"

wget https://raw.githubusercontent.com/acannistra/planet-snowcover/master/sagemaker/lifecycle/imageprocess-no-versions.yml -O "$WORKING_DIR/imageprocess.yml"

conda env update --file "$WORKING_DIR/imageprocess.yml"

pip install --quiet ipykernel

# Customize these lines as necessary to install the required packages

EOF
