About This Project
==================

Motivation
##########

For many ecological modeling tasks, remotely-sensed snow cover measurements are either captured at a spatial scale far too large to be relevant to the study species, or are appropriate in spatial scale but cost-prohibitive (e.g. lidar snow measurements). Models and other mathematical frameworks have shown promise in down-scaling coarse remotely-sensed snow observations, but require technical expertise and data availability. We evaluate the suitability of Planet Labs data, a commercial satellite imagery product with unprecedented spatial (0.8-3 m) and temporal (< 5 day revisit) resolution, for the purpose of acquiring detailed snow-cover and snow-melt data at ecologically-relevant scales. The challenge herein is the radiometric bandwidth available from Planet imagery: only Red, Green, Blue, and Near Infrared bands are measured by these satellites, which makes standard spectral snow cover indices like the Normalized Difference Snow Index unusable. However, advances in machine learning offer tools which are well-suited for this task and lend themselves to experimentation with these new data. We find that a modern convolutional neural network-based image segmentation approach, paired with lidar-derived ground truth snow cover data, produces a robust high-resolution snow-covered area data product.
