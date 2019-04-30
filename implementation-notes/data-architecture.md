# Planet SCA Data Architecture

**Tony Cannistra**, April 2019

The primary design goal of this data architecture is to allow for the creation, storage, and accessibility of spatio-temporally aligned ground-truth/imagery pairs for an ML training workflow. We also take into consideration a future operationalization of these data and models as a secondary design goal.

The data sources which contribute to this project are homogeneous in terms of the tools used to process them, which simplifies the stack of software required. However, because of the nature of remotely-sensed and otherwise stochastically-collected observational data, there are inconsistencies in specific facets of these data which must be accounted for. Examples of these inconsistencies are: slightly variable resolutions, stochastically-overlapping observational footprints, temporal mismatch, and others.

To solve these issues we've based our architecture on the OpenLayers/OpenStreetMap Web Map Tiles standard [specification](https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames) (also known as "slippy map tiles"). This is a spatial data topology which allows for the specification of hierarchically-organized spatial data by chunking the Spherical Mercator projection into square rasters ("tiles"). This specification assigns each tile an `X`, `Y`, and `Z` component, where `X` and `Y` are locations in the Spherical Mercator projection and `Z` represents a "zoom level" – the detail present in each pixel. Implementing this specification ensures that a reference to a given tile from one data source (e.g. `/groundtruth/2124/1235/15.tif`) will represent an identical spatial scale with identical resolution in another (.e.g. `/imagery/2124/1235/15.tif`). This approach was selected because it is an open standard with a large suite of open-source tools. In general, across this work, we choose a zoom level of 15 which has a resolution of 4.773m/pixel. We may transition to zoom level 16, which has a zoom level of 2.837m/pixel in future work. [(Zoom levels info)](https://wiki.openstreetmap.org/wiki/Zoom_levels).

Since the primary objective of this architecture is to train a machine learning model, we treat ground truth data as a first-class citizen within this processing workflow. This means that any processing we do on any imagery begins with a ground-truth raster, because the spatial and temporal extent of these ground-truth observations are the limiting factor in our analysis (see [table](#table:datasource) below).

Here we describe our source data and the methods used to create and store web tiles derived from these data in the cloud.

## Data Sources

This project relies upon spatially-explicit raster data derived from airborne or satellite observation platforms. These data are divided into ground truth observations from the NASA/JPL Airborne Snow Observatory and multispectral imagery from Planet Labs, which will henceforth be referred to as "Ground Truth"  and "Imagery.

<a name="table:datasource"></a>
| data source | derivation | format | reference | resolution | spatial extent | temporal extent |
| ----  | ---- | ---- | ---- | ---- | ---- | ---- |
| Ground Truth | airborne lidar | spatial raster (GeoTIFF) |  https://aso.jpl.nasa.gov/ | 3m | Several Basins: Tuolumne (CA), Merced (CA), San Joaquin (CA), Uncompahgre (CO) | Weekly, Feb 2016 – June 2018 |
| 4-band imagery | Planet Labs cubesat constellation | spatial raster (COGeoTIFF) | [Planet Specification](https://assets.planet.com/docs/Planet_Combined_Imagery_Product_Specs_letter_screen.pdf) | 3m | Global | ~Daily, since 2015 |


## Data Acquisition Workflow --- Ground Truth

The Airborne Snow Observatory data are available from the NSIDC (https://nsidc.org/data/ASO_3M_SD/versions/1). The data are available at watershed scale --- a single ASO collect occupies about 4-6GB of space. We manually select collections based on a research and evaluation plan, which specifies the use of ablation-period collects for maximum evaluative potential for our method.

**Workflow**

1. Acquire ASO collect from NSIDC onto EC2 development instance local storage.
2. Convert to cloud-optimized GeoTIFF using toolkit in `/preprocess` module.
2. Convert ASO collect into binary presence/absence raster by applying a snow depth threshold (defined in research and evaluation plan) via toolkit in `/preprocess` module.
3. Derive a vector polygon describing the extent of snow in ASO collect.
2. Upload raw ASO collect, thresholded COG, and vector snow extent to `planet-snowcover-snow` S3 bucket using original NSIDC identifier as reference.
3. Create zoom-level 15 Web Mercator Tiles using thresholded binary COG in s3 via toolkit in `/preprocess` module. (*this can run anywhere s3 is available*). This process uses the OpenStreetMap "Slippy Map" directory structure, described above and [here](https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames). The average number of zoom-15 tiles for an entire ASO collect is around 3,000.

At the end of this process, the s3 bucket `planet-snowcover-snow` contains the following:
*  A raw ASO Collect raster (GeoTIFF)
*  A cloud-optimized binary raster containing snow extent (cloud-optimized GeoTIFF)
* A shapefile or GeoJSON file containing polygons describing the extent of snow cover from the given collect.
* an Open Street Map "slippy map" directory (defined above) at zoom-level 15 containing the binary thresholded data as `.tif` files.

This approach is repeated for each ASO collect intended for use in model training.

## Data Acquisition Workflow --- Imagery

As mentioned above, the ground truth data source represents our limiting factor in terms of spatial and temporal data availability. Because we are building an architecture which pairs ground truth with imagery for ML training, we construct the following imagery acqusition and processing workflow on the invariant that each image must have a corresponding ground-truth observation. To allow for this, the following workflow borrows components from the previous ground-truth workflow.

For this project we are using the Planet Labs Inc. PlanetScope 4-band analytic surface reflectance data product, (`PSScene4Band-analytic_sr`).

**Workflow**:
  1. Acquire an ASO-derived ground-truth polygon (Shapefile/GeoJSON) describing extent of snow-covered area for a given collect **OR** an observational footprint for an ASO collect.
  2. Using this spatial data and the known date of the ASO collect, select Planet Labs `PSScene4Band` assets using the `analytic_sr` item type with a sufficient spatiotemporal overlap to the ground-truth collect (as specified in research and evaluation plan).
  3. Using the Planet API and the [`porder`](https://github.com/samapriya/porder) CLI, submit an order for imagery. This order contains an operation which subsets the imagery to a given footprint, described above. This operation delivers cloud-optimized GeoTIFF files to the `planet-snowcover-imagery` s3 bucket.
  4. Utilize the `/preprocess` toolkit to create zoom level 15 slippy map tiles for each downloaded image and save to s3.

*For reasons unknown, sometimes an additional step is required to convert the Planet imagery to COG format --- sometimes they do not come that way*.

At the end of this workflow, the `planet-snowcover-imagery` bucket contains raw, spatially-subsetted `PSScene4Band-analytic_sr` TIFF files and zoom-15 Slippy Map directories for each.

## Machine Learning Training Workflow

later
