#!/bin/bash

set -x -u

docker --version
pip install --user awscli
aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
aws configure set default.region us-west-2
export PATH=$PATH:$HOME/.local/bin
eval $(aws ecr get-login --no-include-email --region us-west-2)
docker push "$IMAGE_NAME"
