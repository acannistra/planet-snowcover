**Assessing High-Resolution CubeSat Imagery and Machine Learning for
Detailed, High Resolution Snow-Covered Area.** Anthony F. Cannistra,
Nicoleta Cristea.

**Section X:** *Methods and Data*

We focus our efforts in this study on developing and evaluating a
statistical modeling-based approach to enable the identification of
snow-covered area in high-resolution remote sensing data. We chose
machine learning as our methodological domain after preliminary
experiments demonstrated high potential for these flexible statistical
methods to be well-suited to the challenges presented by these
high-resolution satellite data. Furthermore, the domain of snow-cover
identification is particularly suited to a machine learning-driven
analysis due to the ready availability of high-resolution airborne
lidar-derived snow-cover data, explained further in Sections X.X and
X.X. We construct our model following a standard machine learning
paradigm (described xxx), and choose well-studied focal areas (described
below) as benchmark locations to assess both the absolute performance of
our model compared to ground truth (Section XXX) and relative model
performance across particular variables of interest.

**X.X**: *Study Region*

The two focal regions for this study are the Upper Tuolumne Basin in the
Sierra Nevada mountains of California, USA, and the Gunnison/East River
Basin in the Central Rocky Mountains of Colorado, USA. These regions
were selected for their robust temporal catalog of high-resolution
airborne lidar data from the NASA Airborne Snow Observatory (See Section
X.X), and to create an opportunity for model comparison across
climatological zones.

**X.X:** *Snow Cover Data *

To allow our chosen statistical modeling approach to identify
snow-covered regions in these high-resolution imagery data, our methods
require the use of separate high-resolution snow covered area data to
serve as “ground truth” (see Section X.X). For this we use the NASA/JPL
Airborne Snow Observatory (ASO) data product (Painter et al., 2016).
These data are gridded 3 meter snow depth derived from airborne lidar
collected in chosen watersheds across the western United States. Data
are collected on a weekly basis from mid-winter through complete
snowmelt (February – June) in ASO target basins. We acquired these data
from the National Snow and Ice Data Center’s Distributed Data Access
Center (<https://nsidc.org/data/ASO_3M_SD>). We generate binary snow
masks from these data by applying a threshold of 10cm to the snow depth
field.

**X.X:** *Satellite Imagery*

Planet Labs, Inc. (“Planet”) is a commercial satellite imagery company
that operates the “PlanetScope” constellation of approximately 130 small
(10x10x30cm) satellites in sun-synchronous orbit. This constellation
collects approximately 200 million km^2^ day^-1^ of optical (red, green,
blue, and NIR) land-surface imagery at 3.7m GSD (at nadir) between ±81.5
degrees latitude, with daily nadir revisit times. Two sensor types
(“instruments”) are present in the PlanetScope constellation (“PS2” and
“PS2.SD”) resulting from ongoing sensor development and satellite
launches. These instruments have comparable (but not identical) spectral
band centers and bandwidths (Table X).

          PS2            PS2.SD
  ------- -------------- --------------
  Blue    455 - 515 nm   464 - 517 nm
  Green   500 - 590 nm   547 - 585 nm
  Red     590 - 670 nm   650 - 682 nm
  NIR     780 - 860 nm   846 - 888 nm

**Table X:** Spectral bandwidth of PS2 and PS2.SD instruments within the
PlanetScope constellation, (Planet Labs, Inc., 2019).

For the purposes of this study we consider these instruments to be
identical, and acquire data from each interchangeably.

Planet provides several levels of processing of collected imagery data.
For this study we used the Level 3B PlanetScope “Analytic Ortho Scene,”
an orthorectified multispectral surface reflectance product. Planet’s
atmospheric correction procedure converts top of atmosphere radiance
(derived via coefficients from sensor darkfield and flat field
corrections) to surface reflectance using near-real-time MODIS data
inputs and the 6SV2.1 radiative transfer code (Kotchenova et al., 2008;
Planet Labs, Inc., 2019). This data type is recommended by Planet for
analytic applications.

*Scene Selection and Acquisition*

To pair relatively cloud-free imagery with Airborne Snow Observatory
(ASO) collections (see Sections XXX and XXX), scenes with spatial and
temporal overlap with individual ASO collect spatial footprints were
selected from the Planet imagery catalog. We applied a 3-6 day temporal
buffer to the ASO collection date of interest to ensure a higher
probability of cloud-free imagery acquisition. (Temporal image density
in the Planet catalog has increased dramatically over time, but regions
of ASO collects prior to 2017 often required a larger (5-7 day) buffer
to find spatially-overlapping imagery.) Image candidates were manually
inspected for relative cloud fraction, and images with fewer clouds were
selected for inclusion into our analysis. We used porder version 0.5.7,
an open-source tool (Roy, 2019) for the Planet Orders v2 Application
Programming Interface (API) (Planet Labs, Inc., 2019), to both query the
Planet catalog for imagery data and submit imagery orders. Analytic
Ortho Scene assets were queried via the “PSScene4Band” identifier and
the “analytic\_sr” bundle identifier. We used the Planet Clips API to
acquire only those pixels overlapping our areas of interest (e.g. areas
covered by ASO collect footprints) both to conserve our imagery quota
and reduce data volume. Image assets were delivered from Planet directly
to Amazon Web Services Simple Storage Service (S3) buckets for further
processing.

*Imagery Processing*

**X.X:** *Machine Learning Methodology*

“Machine learning” is a set of statistical techniques to build
predictive models of an outcome variable from data. Models are “trained”
or “fit” to data by selecting a “training” subset of examples from the
population of data. These examples are used to derive a predictive
relationship with the response variable, and each machine learning
technique varies on the precise methodology used to derive this
relationship. Once fit, models are assessed for their ability to
accurately predict response variables given “unseen” samples of data
(the “test” subset) which is disjoint from the training set. In this
study we employed a “supervised learning” approach, wherein the presence
of the response variable in the data (known as a data “label”, in this
case lidar-derived snow presence) guides the search for a statistical
relationship between the input data (“features”) and the response
(“label”). Once a supervised learning model is fit using data that
contains the response variable, the resulting statistical relationship
can be employed to predict the response variable from unlabeled data.

Identifying the spatial extent and categorical classification of regions
within images is known as “image segmentation” or “instance
segmentation” (CITE?). Classification of snow in satellite imagery fits
well within this task definition, and this allowed us to use machine
learning techniques specific to image segmentation. In our version of
the task, the four bands of PlanetScope imagery in each pixel (red,
green, blue, NIR; see Section XXX) represent the input data to our model
(the “features”), and airborne lidar-derived binary snow masks (see
Section XXX) represent the response variable (“labels”).

We employ a neural network to accomplish this image segmentation task.
Neural networks are specific types of machine learning methods designed
to extract statistically meaningful linear combinations of input
features from data (PlanetScope bands) and model a dependent variable
(snow presence/absence) as a nonlinear function of these derived linear
combinations (Hastie et al., 2009, Section 11.1). We chose a method
based on a network architecture demonstrated to perform very well in
biomedical image segmentation (Known as the "U-Net" architecture;
Ronneberger et al., 2015) and modified to perform well with satellite
remote sensing imagery. The resulting network, known as TernausNetV2 and
developed by Iglovikov et al., provides state-of-the-art satellite image
segmentation when applied to the task of building detection in satellite
imagery (Iglovikov et al., 2018). To our knowledge this method has not
been applied to the segmentation of snow in satellite imagery.

**Section X.X:** *Model Training *

*This file was autogenerated from artifacts/manuscript/methods_draft.docx*
