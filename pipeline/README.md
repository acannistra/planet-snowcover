# `planet-snowcover` Pipeline Tutorial

**Tony Cannistra, 2019**

This document details the processing pipeline we've developed to leverage Planet Labs imagery via a neural network and lidar-derived ground truth snow cover to create a high-resolution snow covered area mask. It consists of a set of Python notebooks, which implement the following set of tasks:

![infr](../images/schematic.png)

This pipeline is a combination of Jupyter notebooks, custom preprocessing code, open source command line tools, and Docker containers which run on Amazon Web Services infrastructure. While we've intended to make these notebooks as basic as possible, they require a basic understanding of AWS infrastructure (specifically EC2, S3, and Sagemaker). However, almost all of the code is infrastructure-agnostic.


## Table of Contents

1. Ground Truth Acquisition and Processing
2. Imagery Acquisition and Processing
2. Neural Network Configuration
3. Model Training and Evaluation
4. Snow Mask creation

## Ground Truth Acquisition and Processing
**Notebook**: [`X_Acquire_ASO.ipynb`](X_Acquire_ASO.html)

The root of this image processing pipeline is the ground truth labeling, because it is the limiting factor to training the neural network. Put another way, we can't train the neural network on imagery for which we have no ground truth information, because the network has no foundation for its learning. As such, this pipeline begins with the identification, acqusition, and preprocessing of ground truth information.

For the snow-cover case, NASA/JPL Airborne Snow Observatory data serves as our ground truth. [`X_Acquire_ASO.ipynb`](X_Acquire_ASO.html) is the notebook which performs this part of the workflow.

## Imagery Acquisition and Processing
**Notebook**:[`X_Planet_Ordering.ipynb`][X_Planet_Ordering.html]

The next step in the processing workflow is to use the spatial footprint of the ASO collect acquired in the previous step to acquire imagery from Planet Labs over the area specified in the footprint.

## Neural Network Configuration
