# Environment Configuration Notes

This analysis is dependent upon a matrix of complicated dependencies due to the complexities of dealing with raster data. This document intends to document some of those configuration shenanigans.

## AWS Notes

**Instance Type**: `c4.large` / `c4.xlarge`.
**AMI** : At first just the Amazon Linux AMI, but then the Deep Learning (Ubuntu) AMI. 

## Package Notes

* Don't install geopandas/fiona with conda in the `tensorflow_p36` environment. It doesn't work (`ImportError` from Fiona, some GDAL dependency not being accounted for. Seems like `pip` can handle it though. 
* Installing `rasterio` on the Deep Learning AMI was a bit of a bear. I think because of a complex GEOS/GDAL dependency we need to build from source:
  * `sudo add-apt-repository ppa:ubuntugis/ppa`
  * `sudo apt-get update`
  * `sudo apt-get install gdal-bin libgdal-dev`
  * `pip install rasterio --no-binary rasterio` (**important to build from source**) 
* Seems like it doesn't matter if `rasterio` or `geopandas` is installed first. 
