# Notebooks

These notebooks represent the meat of the analysis, from image acquisition and processing to machine learning. 

## `ml-v1.ipynb`
An initial attempt at using a gaussian process classifier with an RBF kernel to classify snow vs non-snow at Mt. Rainier. Very good accuracy in cross-validation. 

## `ASO-extract.ipynb`
Utilities for managing NASA/JPL Airborne Snow Observatory (ASO) snow observations. 

## `ml-v4-ASO.ipynb` and `ml-verify-ASO.ipynb`
Model training and quantitaive/qualitative evaluation on ASO-based data. 

## `mlverify-image.ipynb`
Qualitative assessment of snow cover performance on actual imagery. 

## `pipeline-all-with-download.ipynb`
Contains all of the code which went into understanding the Planet API, and uses some abstractions around it for simplicity. 

## `data-extract.ipynb`
Experimental code for extracting neighboring pixels from images around ground-truth measurement sites and outputting a CSV. 

## `data-exploration.ipynb`
Contains code for initial exploratory data analysis, including some histograms of snow-on vs snow-off conditions and some clustering. 
