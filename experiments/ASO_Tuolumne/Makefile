SHELL=/bin/bash

VALIDATION_MASKS ?= s3://planet-snowcover-snow-2/
VALIDATION_IMAGES ?= s3://planet-snowcover-imagery-2/

MODEL_TRAIN_CONFIG ?= s3://planet-snowcover-experiments-2/co-train.toml
MODEL_LOCATION ?= s3://planet-snowcover-experiments-2/planet-snowcover-2020-03-12-02-43-15-610
MODEL_NAME ?= checkpoint-00050-of-00050.pth

RSP ?= model/robosat_pink

RUN_WORKDIR = $(shell date +"%m-%d-%Y-%T")
RUN_WORKDIR := ${RUN_WORKDIR}

.PHONY: verify_creds
verify_creds:
ifeq ($(and $(AWS_SECRET_ACCESS_KEY), $(AWS_ACCESS_KEY_ID)), )
	$(error "AWS Credentials unavailable. Check credentials.")
endif

all: setup_aws config run_prediction cleanup_aws

setup_aws: verify_creds
ifeq (,$(wildcard ~/.aws/credentials/))
	echo "Creating new AWS Credentials file."
	mkdir -p ~/.aws/
	echo "[default]" >> ~/.aws/credentials
	echo "aws_access_key_id="$(AWS_ACCESS_KEY_ID) >> ~/.aws/credentials
	echo "aws_secret_access_key="$(AWS_SECRET_ACCESS_KEY) >> ~/.aws/credentials
else
	echo "Backing up AWS Credentials File"
	mv ~/.aws/credentials ~/.aws/credentials.bak
	echo "[default]" >> ~/.aws/credentials
	echo "aws_access_key_id="$(AWS_ACCESS_KEY_ID) >> ~/.aws/credentials
	echo "aws_secret_access_key="$(AWS_SECRET_ACCESS_KEY) >> ~/.aws/credentials
endif

cleanup_aws:
ifeq (,$(wildcard ~/.aws/credentials.bak))
	rm ~/.aws/credentials
else
	mv ~/.aws/credentials.bak ~/.aws/credentials
endif

setup_dir:
	mkdir -p "$(RUN_WORKDIR)/prediction"

config: setup_dir
ifeq ( $(findstring $(MODEL_TRAIN_CONFIG), s3), )
		cp "$(MODEL_TRAIN_CONFIG)" "$(RUN_WORKDIR)/config.toml"
else
		aws --profile default s3 cp "$(MODEL_TRAIN_CONFIG)" "$(RUN_WORKDIR)/config.toml"
endif


run_prediction: config
	cd $(RSP) && \
		echo "./rsp predict --create_tif \
		--checkpoint $(MODEL_LOCATION)/$(MODEL_NAME) \
		--aws_profile default \
		--tiles $(VALIDATION_IMAGERY)\
		--buffer --config \"$(abspath $(RUN_WORKDIR))/config.toml\" \
		\"$(abspath $(RUN_WORKDIR))/prediction\""

# .PHONY cleanup
# cleanup:
