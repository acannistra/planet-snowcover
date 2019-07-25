[osm_tiles]: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
[aso]: https://aso.jpl.nasa.gov
[snowex]: https://neptune.gsfc.nasa.gov/hsb/index.php?section=322

# ML Model Design

This document details the design for a machine learning training and evaluation pipeline to successfully fulfill a ground truth-based satellite imagery snow cover identification task.

__Goal__: produce a model which can identify snow in 3m PlanetScope satellite imagery with sufficient accuracy for [operational use](#operational_use_cases).

## Previous Work

Our [previous approach](../notebooks/ml-v4-ASO.ipynb) used a Gaussian Process approach to create a pixel-based snow classifier. The results were mixed. We're hoping to expand based on developments in image segmentation networks.

## Current Design

The framework we're using for this task is an "image segmentation" modeling framework, which relies on three elements:
1. Images of known, consistent sizes
2. Binary masks corresponding to the desired segmentation for each image, with matching sizes
3. A network architecture (_with or without pre-trained weights?_) for image segmentation

### Input Data

| Data | Data Type | Description|
| ---- | --------- | -----------|
| PlanetScope Image Tiles | 4-band rasters | Using the `../preprocess` tools we've created a set of 4-band TIFF image tiles which are stored in [OSM/XYZ tile format][osm_tiles] and represent imagery relevant to the known ground-truth. |
| Ground Truth Tiles| Binary rasters | Again using `../preprocess` toosl we've created a set of 1-band binary TIFF image tiles (in [OSM/XYZ][osm_tiles]) which represent our segmentation masks. __Note:__ These tiles cover an extent _at least as large_ as the image tiles. The ground-truth data can come from a variety of sources, including: __1)__ the [Airborne Snow Observatory (ASO)][aso] and __2)__ [SnowEX][snowex]

### Model Architectures

TBD, but
* [Mapbox Robosat U-Net](https://github.com/mapbox/robosat/blob/master/robosat/unet.py)
* [Standard/pre-trained U-Net](https://arxiv.org/abs/1505.04597)
* [TernausNet/TernausNetV2](https://github.com/ternaus/TernausNetV2)


### Training

We need to figure out how to structure this training task, because the data are strange. Though we have input data as [above](#input_data), it's really stored on disk in slippy-map tile directories _for each Planet image_. The options for incoporating these data into a training pipeline are as follows:

* Concatenate all tiles from all images into a `/image-tiles` folder.
  * **Pros**: training code / data loader is easy and straightforward.
  * **Cons**: lose geospatial information in the form of XYZ directory structure, which makes serving results harder? Need to assign unique IDs to each image.
* Write a data loader which does this concatenation given a list of folders which themselves are slippy map directories.
  * **Pros**: means we can keep the data stored in the current way (which is produced in the `preprocess` step)
  * **Cons**: would be pretty precise + brittle to implement this and to ensure overlap with the correct mask tile
* Train with checkpoints: train model incrementally using only a single image (e.g. a single XYZ directory) for each training step and using model checkpoints to continue training.
  * **Pros:** allows for maintainance of the current directory structure and for easy train-test split (if we split on images!)
  * **Cons:** there's got to be some sort of training bias lurking in here. Difficult train-test split (if we split on tiles!)

I've decided that the best first-pass at this is to just concatenate all images together into an `/image-tiles` folder, which has several implementation advantages. The loss of geoaptial information isn't terribly important (especially when the .tif files themselves are GeoTiffs.)

## Operational Use Cases

* Ecology: _studying changes in alpine phenology_ (Janneke HilleRisLambers)
* Ecology: _abiotic environmental variable for species distribution modeling_
* Avalanche Forecasting: _early season snow extent for basal weak layer prediction_ (Deems)
