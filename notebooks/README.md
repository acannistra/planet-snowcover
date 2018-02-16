# Data Exploration and Download Notebooks

The notebooks in this directory are the experimental launch points for the image utilities in `../image_utils` and `../scripts`. They also have some preliminary image analysis in them. It's probably stupid, and is definitely wrong. 

## `ml-v1.ipynb`
An initial attempt at using a gaussian process classifier with an RBF kernel to classify snow vs non-snow. Very good accuracy. No classification of unseen image pixels yet though. 

## `pipeline-all-with-download.ipynb`
Contains all of the code which went into understanding the Planet API, and uses some abstractions around it for simplicity. 

## `data-extract.ipynb`
Experimental code for extracting neighboring pixels from images around ground-truth measurement sites and outputting a CSV. 

## `data-exploration.ipynb`
Contains code for initial exploratory data analysis, including some histograms of snow-on vs snow-off conditions and some clustering. 
