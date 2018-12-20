This file contains a design for a [Google Cloud Dataflow (GCD)](https://cloud.google.com/dataflow/docs/) pipeline for preparing images for machine learning.



## GCD Pipeline Design Considerations

The purpose of this pipeline is to merge raw ground truth data with imagery for the production of a set of standardized image tiles for the purpose of training a machine learning model.

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
