SHELL=/bin/bash

VALIDATION_BUCKET ?= s3://planet-snowcover-validation/
VALIDATION_MASKDIR ?= mask_tiles
VALIDATION_IMAGEDIR ?= image_tiles

MODEL_TRAIN_CONFIG ?= s3://planet-snowcover-experiments-2/co-train.toml
MODEL_LOCATION ?= s3://planet-snowcover-experiments-2/planet-snowcover-2020-03-12-02-43-15-610
MODEL_NAME ?= checkpoint-00050-of-00050.pth

RSP ?= ../../model/robosat_pink

RUN_WORKDIR = $(shell date +"%m-%d-%Y-%T")

.PHONY: verify_token
verify_token:
ifeq ($(AWS_SECRET_ACCESS_KEY) && $(AWS_ACCESS_KEY_ID), )
	$(error "AWS Token unavailable. Check credentials.")
endif

all: setup_aws config cleanup_aws

setup_aws: verify_token
ifeq ( $(wildcard ~/.aws/credentials) , )
	mkdir -p ~/.aws/
  echo "[default]" >> ~/.aws/credentials
	echo "aws_access_key_id="$(AWS_ACCESS_KEY_ID) >> ~/.aws/credentials
	echo "aws_secret_access_key="$(AWS_SECRET_ACCESS_KEY) >> ~/.aws/credentials
else
	mv ~/.aws/credentials ~/.aws/credentials.bak
	echo "[default]" >> ~/.aws/credentials
	echo "aws_access_key_id="$(AWS_ACCESS_KEY_ID) >> ~/.aws/credentials
	echo "aws_secret_access_key="$(AWS_SECRET_ACCESS_KEY) >> ~/.aws/credentials
endif

cleanup_aws:
ifeq ( $(wildcard ~/.aws/credentials.bak), )
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
		./rsp predict --create_tif \
		--checkpoint $(MODEL_LOCATION)/$(MODEL_NAME)
		--aws_profile default
		--buffer --config "$(abspath $(RUN_WORKDIR))" \
		"$(abspath $(RUN_WORKDIR))/prediction"

# .PHONY cleanup
# cleanup:
