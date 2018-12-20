This file contains a design for a [Google Kubeflow](https://cloud.google.com/blog/products/ai-machine-learning/getting-started-kubeflow-pipelines)/[Google Cloud Dataflow](https://cloud.google.com/dataflow/) pipeline for preparing satellite images for machine learning via a raster or vector-based ground-truth label set. GCP's Kubeflow pipelines service is a managed containerized pipeline service which allows for distributed execution of a Docker-based processing pipeline.


## Pipeline Design Considerations

The purpose of this pipeline is to merge raw ground truth data with imagery for the production of a set of standardized image tiles for the purpose of training a machine learning model.

This particular implementation assumes a desired output of paired (data, mask) tilesets.


**Inputs**

| Name | Data Type | Description |   
| ---- | --------- | ----------- |
| Ground Truth | Raster File (`.tif`, `.jp2`, etc) or Vector File (`.shp`, `.geojson`) | Contains information about ground state (in this case, snow presence or absence) as measured by another method (e.g. ASO/SnowEX lidar). Can either be a GeoJson binary vector or a raw or binary raster.
| Date | string or `datetime` | date of ground truth data acqusition. Used to determine which imagery to acquire.|
| Date Range | integer | number of days around ground truth acqusition date to search for imagery.

**Outputs**

| Name | Data Type | Description |
| ---- | -----     | ----        |
| Image Tiles | Cloud Storage bucket (S3, GCS) | Bucket with either `{z}/{x}/{y}.png` structure or `{z}_{x}_{y}.png` filenames containing tiles. |
| Mask Tiles | Cloud Storage Bucket (S3, GCS) | Bucket with either `{z}/{x}/{y}.png` structure or `{z}_{x}_{y}.png` filenames containing binary masks for training. |

The output __Image Tiles__ are cropped to the extent of the ground truth information. The set of __Image Tiles__ and __Mask Tiles__ is identical.

### Conceptual Workflow

The primary steps to completing this data transformation are 1) ground truth pre-processing, 2) image acquisition and storage, 3) image preprocessing, 4) image and mask tiling.

#### Ground Truth Preprocessing

| input parameter | description |
| ----  | ---- |
| __`--gt_file`__ | ground truth data file, as below|  
|  _`--threshold`_ (optional) | threshold for real-valued raster input|

Ground truth data can come in the form of either a GeoJSON file containing the spatial extent of the desired segmentation (e.g. snow locations) as a `Polygon`, or as a raster file (GeoTIFF, JP2). These raster files, in practice, are either binary (similar to vectors) or have real values in them (e.g. lidar snow depth) which must be thresholded to create a mask.

We must accept all three of these input data types and process them as follows:

| Input Data Type | Processing Strategy |
| ---- | ---- |
| binary raster | No processing needed --- can proceed directly to tiling.  |
| real-valued raster | Must be thresholded (__need a `--threshold` pipeline parameter__) to a binary raster. |
| binary vector | Must be converted to binary raster. |  

__Output__: this stage of the pipeline places in cloud storage the binary raster produced via this processing step and outputs its location for use by future steps. It also produces a `.GeoJSON` file containing the spatial extent of the ground truth for use by the image acquisition step.

#### Image Acquisition

| input parameter | description |
| ----  | ---- |
| __`--gt_date`__ | date of ground truth acquisition |
| __`--date_range`__ | number of days around `gt_date` to search for imagery in catalog |  
| _`--max_images`_ (optional) | used to constrain the number of images downloaded |

Using the `gt_date` and `date_range` parameters we compute a date range to search the imagery catalog for. We also use the GeoJSON output from __step 1__ to geographically constrain the imagery search. Eventually this process will be imagery-agnostic, but we currently implement using the Planet Labs API.

__Open Questions__:
* How do we select what images to download? Cloud cover? Sort by date?
* Do we select images that overlap spatially but not in time? (e.g. what if the same meter of Earth is covered by several images on different days --- do we just select closest to `gt_date`?)

__Output:__ A cloud storage bucket containing GeoTIFF files representing raw 4-band images cropped to the extent of the ground truth dataset.



#### Image Preprocessing

Not totally sure what goes in here but I'm sure we're going to want to do something to the imagery before it gets tiled. Perhaps a TOA correction or some such thing. Wanted to leave room for it.

#### Tiling

| input parameter | description |
| ----- | ----- |

Three steps here:

1. Tile the binary raster data mask into cloud storage bucket.
1. Tile all images into cloud storage bucket.
1. Be sure that all image tiles have a paired ground truth tile and that there are no orphan tiles.
1. Come up with some sort of standardized directory structure (maybe best to stick with XYZ/OSM tiles here and reorganize later for training?)

__Output:__ A cloud storage bucket containing an `/images` and `/masks` directory
