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

**X.1**: *Study Region*

The two focal regions for this study are the Upper Tuolumne Basin in the
Sierra Nevada mountains of California, USA, and the Gunnison/East River
Basin in the Central Rocky Mountains of Colorado, USA. These regions
were selected for their robust temporal catalog of high-resolution
airborne lidar data from the NASA Airborne Snow Observatory (See Section
X.X), and to create an opportunity for model comparison across
climatological zones.

**X.2:** *Snow Cover Data *

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
Center (<https://nsidc.org/data/ASO_3M_SD>). We generate binary snow on
/ snow off masks from these data by applying a threshold of 10cm to the
snow depth field.

**X.3:** *Satellite Imagery*

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
PlanetScope constellation, (Planet Labs, Inc., 2019a).

For the purposes of this study we consider these instruments to be
identical, and acquire data from each interchangeably. This choice was
motivated by our intent to construct a method that can leverage the
entire temporal extent of the Planet imagery catalog.

Planet provides several levels of processing of collected imagery data.
For this study we used the Level 3B PlanetScope “Analytic Ortho Scene,”
an orthorectified multispectral surface reflectance data product.
Planet’s data processing procedure converts top of atmosphere radiance
(derived by applying sensor darkfield and flat field corrections to raw
image sensor data) to surface reflectance using near-real-time MODIS
data inputs and the 6SV2.1 radiative transfer code (Kotchenova et al.,
2008; Planet Labs, Inc., 2019a). This data type is recommended by Planet
for analytic applications.

**X.3.1:** *Scene Selection and Acquisition*

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
Programming Interface (API) (Planet Labs, Inc., 2019b), to both query
the Planet catalog for imagery data and submit imagery orders. Analytic
Ortho Scene assets were queried via the “PSScene4Band” identifier and
the “analytic\_sr” bundle identifier. We used the Planet Clips API to
acquire only those pixels overlapping our areas of interest (e.g. areas
covered by ASO collect footprints) both to conserve our imagery quota
and reduce data volume. Image assets were delivered from Planet directly
to Amazon Web Services Simple Storage Service (S3) buckets for further
processing.

**X.4:** *Machine Learning Methodology*

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

**X.5:** *Cyberinfrastructure & Model Training*

Training a neural network is a computationally-demanding task requiring
access to large quantities of data and specialized hardware. In
particular, computers with access to large memory and graphics
processing units (GPUs) greatly shorten the training time for our model
and enable quicker experimentation. In addition, the large volume of
both airborne lidar and satellite imagery data co-located with our study
sites required us to have access to large data storage facilities. For
these reasons we chose the compute and storage resources provided by
Amazon Web Services (AWS), a commercial cloud service provider, to
enable our training procedure.

**X.5.1:** *Data Preprocessing*

Once acquired, imagery and airborne lidar-derived snow masks are stored
as single or multiband GeoTIFF files (Open Geospatial Consortium, 2019)
in AWS Simple Storage Service (S3) “buckets” to enable access by further
processing tools. To enable co-registration of the snow mask data with
imagery data and produce standardized “data units” required by neural
network training, we then divide the raw imagery and snow mask data into
512 by 512 pixel images, or “tiles,” derived from a standardized global
grid. We use the Spherical Web Mercator Spherical Tile standard
(sometimes referred to as the “slippy map” tile standard due to their
employment in interactive mapping applications) to define the grid of
tiles (OpenStreetMap, 2019), and use the “mercantile,” “rasterio,” and
“rio-tiler” open-source software packages to enable gridding and storage
of these images (Mapbox, Inc., 2019; Vincent, 2019). The spherical Web
Mercator tile standard assigns a unique spatially-explicit identifier to
each 512x512 pixel image tile, which can then be used to align imagery
tiles and snow mask tiles (e.g. the tiles “snow/1/2/3.tif” and
“image/1/2/3.tif” have identical spatial extent). These tiles are stored
as GeoTIFF files in AWS S3 buckets tagged with their image or ASO
collection identifiers and dates of collection. This preprocessing
effort is completed via Jupyter notebooks (Kluyver et al., 2016) on AWS
Elastic Compute Cloud (EC2) compute instances (see Figure X).

![](media/image1.png)**Figure X:** Schematic of data preprocessing
procedure for co-located Planet Labs Inc. satellite imagery and Airborne
Snow Observatory snow mask data via Amazon Web Services cloud
infrastructure.

**X.5.2:** *Model Training*

Our implementation of the training procedure is based in the Python
programming language (v.3.5; Python Software Foundation,
<https://www.python.org>) using PyTorch (Paszke et al., 2019), and is a
heavily modified version of the “robosat.pink” software, an open-source
set of command-line tools to enable machine learning with satellite
imagery via the TernausNetV2 image segmentation network (Courtin and
Hofmann, 2019; Iglovikov et al., 2018). The original software in this
package was developed for three band remote sensing imagery and as such
was not able to leverage multispectral data. We modified the package to
enable the use of any N-band multispectral imagery data product and to
allow for the use of cloud-based data storage and computation
infrastructure.

To allow for quicker experimentation and simpler reproducibility, we
packaged the training code, dependencies, and other software for our
neural network implementation into a platform-agnostic computational
working environment (or “container”) via Docker (Merkel, 2014). We used
the AWS “SageMaker” service to manage the training of our network, which
greatly simplified experimentation with different network
parameterizations and datasets. We chose the “p2\_xlarge” AWS EC2
instance type for our training, as it afforded sufficient memory and
graphics processing units for the training task.

We produced several different models for this study in order to assess
the effects of training procedure on the final predictive accuracy. Each
of our models was trained using data from a single Airborne Snow
Observatory collection site (Upper Tuolumne Basin, California, USA or
Gunnison/East River Basin, Colorado, USA). We pair a given set of binary
snow mask tiles corresponding to a single ASO collection with the
corresponding set of imagery tiles (with potentially some duplicates due
to multiple Planet imagery collections within the temporal imagery
search window), and divide this set of image-mask pairs into training
and testing subsets via a 70%/30% split. This technique ensures that
only images that spatially and temporally overlap the ASO data are
included in the training. Each training effort undergoes 50 epochs with
a batch size of 7 and a learning rate of 2.5 x 10^-5^. The resulting
model parameter weights are saved into an AWS S3 bucket. If there are
multiple ASO collect dates for a single site, we repeat the above
procedure for any additional ASO collections, but we initialize the
model training procedure with the weights derived from the previous
model training run. This allows the training process to build upon
previous training runs.

**X.6:** *Performance Evaluation*

To assess the relative ability of our trained models to identify snow in
Planet imagery, we designed an assessment scheme which allowed us to
compare the snow identification skill of our models to the snow
identification performance of several other state-of-the-art
remotely-sensed snow-covered area data products. The high accuracy of
the Airborne Snow Observatory data (Painter et al., 2016) allowed us to
consider ASO snow-cover data to be a “ground truth” snow covered area
dataset, against which we compare all other SCA data products, including
our own. For each comparable snow-covered area dataset, described below,
we computed several metrics of pixel classification with reference to a
spatially and temporally overlapping ASO observation. The metrics we
computed are:

-   Precision, which computes the percentage of snow classifications
    predicted by our model that are also snow classifications in in the
    compared dataset:

$$Precision = \ \frac{\text{True\ Positives}}{\text{True\ Positives}\  + \ \text{False\ Positives}}$$

-   Recall, which computes the percentage of true snow classifications
    which are also true snow classifications predicted by our model:

$$Recall = \ \frac{\text{True\ Positives}}{\text{True\ Positives}\  + \ \text{False\ Negatives}}$$

-   F-Score or F1 score, which is the harmonic mean of precision and
    recall:

$$\text{\ FScore} = 2 \bullet \frac{\text{Precision}\  \times \ Recall}{Precision + Recall}$$

-   Balanced accuracy, which normalizes the true positive and true
    negative predictions by the number of true positive and true
    negative samples to allow for a less biased assessment of accuracy
    given the relative accuracy of each prediction type:

$$\text{Balanced\ Accuracy} = \frac{True\ Positive\ Rate + True\ Negative\ Rate}{2}$$

Using these metrics we assessed the relative performance of our model
predictions compared to several other snow covered area datasets. These
datasets are described in Table X.

  Data              Observation Type   Spatial Resolution   Temporal Resolution              Binarization Procedure       Reference
  ----------------- ------------------ -------------------- -------------------------------- ---------------------------- ------------------------------------------------------------------------------
  ASO Snow Depth    Airborne lidar     3m                   Weekly, during ablation season   *Threshold*: Depth \> 10cm   Painter et al., 2016
  MODIS fSCA        Satellite          500m                 Daily                            *Threshold*: XX              Hall, 2015
  Sentinel 2 NDSI   Satellite          10m                  5 days                           *Threshold*: NDSI \> 0.42    Drusch et al., 2012
  Landsat 8 fSCA    Satellite          30m                  16 Days                          *Threshold*: fSCA \> 0       U.S. Geological Survey, Earth Resources Observation And Science Center, 2018

**Table X**: Snow covered area datasets used for comparison to model
predictions. “Binarization procedure” column describes technique used to
derive binary snow presence mask from continuous snow presence fields in
each dataset for comparison to model predictions.

To evaluate performance of our model in the context of these datasets,
we chose a full Planet scene (in contrast to image tiles) and ASO
observation pair which was either part of a test subset during model
training or not part of any model training procedure to ensure no data
used in model training is used for model assessment. We then computed a
model prediction of snow covered area for this image scene using the
best-performing model trained in the same geographic region as the image
(e.g., a model trained using imagery and ASO data from California would
be used to predict snow presence or absence on our test image over
California). A single spatially co-located observation from each of the
above datasets was then acquired within a 5-15 day window of the image
acquisition time. Most of these datasets contain a continuous snow cover
field per observation pixel; since our model produces binary pixel
classification, we use a binarization procedure for each dataset to
produce a binary snow mask for comparison to our method. The metrics
described above were then computed with reference to a contemporaneous
binarized ASO collection for each SCA dataset, including our model, and
relative performance was compared.

In addition to the above metrics we also evaluate our model’s ability to
act as a temporal “gap filling” method for other observational snow
cover datasets with coarser temporal scale, such as MODIS fSCA or
Landsat 8 fSCA. To do this, we up-sample (or “coarsen”) both our
model-derived snow masks and the binary ASO snow mask to match the
resolution of a coarser data product. This up-sampling procedure
produces a “pseudo-fSCA” product for both our model-derived masks and
the ASO mask by computing the percentage of higher-resolution “snow
present” pixels within a single coarsened pixel. We then compute the
mean difference in fSCA between the coarser image product (MODIS fSCA or
Landsat 8 fSCA) and ASO-derived pseudo-fSCA across a test image. We
compare this to the mean difference in fSCA between the coarser image
product and our model-derived pseudo-fSCA. The relative difference in
these values allows us to assess how comparable our model is to the
coarser data product with reference to an ASO-derived ground truth fSCA.

***Literature Cited***

Courtin, O., Hofmann, D.J., 2019. RoboSat.pink Computer Vision framework
for GeoSpatial Imagery. DataPink.

Drusch, M., Del Bello, U., Carlier, S., Colin, O., Fernandez, V.,
Gascon, F., Hoersch, B., Isola, C., Laberinti, P., Martimort, P.,
Meygret, A., Spoto, F., Sy, O., Marchese, F., Bargellini, P., 2012.
Sentinel-2: ESA’s Optical High-Resolution Mission for GMES Operational
Services. Remote Sensing of Environment, The Sentinel Missions - New
Opportunities for Science 120, 25–36.
https://doi.org/10.1016/j.rse.2011.11.026

Hall, D.K., 2015. MODIS/Terra Snow Cover Daily L3 Global 500m SIN Grid.
https://doi.org/10.5067/MODIS/MOD10A1.006

Hastie, T., Tibshirani, R., Friedman, J., 2009. The Elements of
Statistical Learning. Springer New York, New York, NY.

Iglovikov, V.I., Seferbekov, S., Buslaev, A.V., Shvets, A., 2018.
TernausNetV2: Fully Convolutional Network for Instance Segmentation.
arXiv:1806.00844 [cs].

Kluyver, T., Ragan-Kelley, B., Pérez, F., Granger, B.E., Bussonnier, M.,
Frederic, J., Kelley, K., Hamrick, J.B., Grout, J., Corlay, S., Ivanov,
P., Avila, D., Abdalla, S., Willing, C., al, et, 2016. Jupyter
Notebooks - a publishing format for reproducible computational
workflows, in: ELPUB.

Kotchenova, S.Y., Vermote, E.F., Levy, R., Lyapustin, A., 2008.
Radiative transfer codes for atmospheric correction and aerosol
retrieval: intercomparison study. Appl. Opt. 47, 2215.
https://doi.org/10.1364/AO.47.002215

Mapbox, Inc., 2019. Mercantile [WWW Document]. URL
https://github.com/mapbox/mercantile

Merkel, D., 2014. Docker. Linux Journal.

Open Geospatial Consortium, 2019. GeoTIFF Standard 115.

OpenStreetMap, 2019. Slippy Map Tilenames [WWW Document]. URL
https://wiki.openstreetmap.org/wiki/Slippy\_map\_tilenames

Painter, T.H., Berisford, D.F., Boardman, J.W., Bormann, K.J., Deems,
J.S., Gehrke, F., Hedrick, A., Joyce, M., Laidlaw, R., Marks, D.,
Mattmann, C., McGurk, B., Ramirez, P., Richardson, M., Skiles, S.M.,
Seidel, F.C., Winstral, A., 2016. The Airborne Snow Observatory: Fusion
of scanning lidar, imaging spectrometer, and physically-based modeling
for mapping snow water equivalent and snow albedo. Remote Sensing of
Environment 184, 139–152. https://doi.org/10.1016/J.RSE.2016.06.018

Paszke, A., Gross, S., Massa, F., Lerer, A., Bradbury, J., Chanan, G.,
Killeen, T., Lin, Z., Gimelshein, N., Antiga, L., Desmaison, A., Kopf,
A., Yang, E., DeVito, Z., Raison, M., Tejani, A., Chilamkurthy, S.,
Steiner, B., Fang, L., Bai, J., Chintala, S., 2019. PyTorch: An
Imperative Style, High-Performance Deep Learning Library, in: Wallach,
H., Larochelle, H., Beygelzimer, A., Alché-Buc, F. d\\textquotesingle,
Fox, E., Garnett, R. (Eds.), Advances in Neural Information Processing
Systems 32. Curran Associates, Inc., pp. 8024–8035.

Planet Labs, Inc., 2019a. Planet Imagery Product Specifications.

Planet Labs, Inc., 2019b. Planet Developer Resource Center [WWW
Document]. URL https://developers.planet.com/docs/orders/ (accessed
1.10.20).

Ronneberger, O., Fischer, P., Brox, T., 2015. U-Net: Convolutional
Networks for Biomedical Image Segmentation. arXiv:1505.04597 [cs].

Roy, S., 2019. samapriya/porder: porder: Simple CLI for Planet ordersV2
API. Zenodo. https://doi.org/10.5281/zenodo.3575881

U.S. Geological Survey, Earth Resources Observation And Science Center,
2018. Collection-1 Landsat Level-3 Fractional Snow Covered Area (FSCA)
Science Product. https://doi.org/10.5066/F7XK8DS5

Vincent, S., 2019. rio-tiler.

*This file was autogenerated from artifacts/manuscript/methods_draft.docx*
