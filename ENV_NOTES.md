# Environment Configuration Notes

This analysis is dependent upon a matrix of complicated dependencies due to the complexities of dealing with raster data. This document intends to document some of those configuration shenanigans.

## AWS Notes

**Instance Type**: `c4.large` / `c4.xlarge`.
**AMI** : At first just the Amazon Linux AMI, but then the Deep Learning (Ubuntu) AMI. 

## Package Notes

* Don't install geopandas/fiona with conda in the `tensorflow_p36` environment. It doesn't work (`ImportError` from Fiona).
