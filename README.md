<div style="text-align:center; padding-left: 10%; padding-right: 10%">

# Planet Snowcover [![Documentation Status](https://readthedocs.org/projects/planet-snowcover/badge/?version=latest)](https://planet-snowcover.readthedocs.io/en/latest/?badge=latest)


Planet Snowcover is a project that pairs airborne lidar and Planet Labs satellite imagery with cutting-edge computer vision techniques to identify snow-covered area at unprecedented spatial and temporal resolutions.

**Researchers**: *[Tony Cannistra](https://www.anthonycannistra.com)<sup>1</sup>, David Shean<sup>2</sup>, and Nicoleta Cristea<sup>2</sup>*

<img src="./artifacts/co-ex-1.png">

</div>

<div><small>1: Department of Biology, University of Washington, Seattle, WA.</br>2: Department of Civil and Environmental Engineering, University of Washington, Seattle, WA</small>

## This Repository

This repository serves as the canonical source for the software and infrastructure necessary to sucessfully build and deploy a machine-learning based snow classifier using Planet Labs imagery and airborne lidar data.

* [Primary Components](#primary-components)
* [Requirements](#requirements)
  * [Basic Requirements](#basic-requirements)
  * [Development Requirements](#development-requirements)
  * [Accounts + Data](#accounts-and-data)
* [Infrastructure Deployment](#infrastructure-deployment)
* [Tutorials](#tutorials)
* [Implementation Details](#implementation-details)
  * AWS Cloud Resources
  * Open Source Machine Learning
* Funding Sources
* [Original Research Proposal](#original-proposal)

## Primary Components

The contents of this repository are divided into several main components, which we detail here. This is the place to look if you're looking for something in particular.

| Folder                                             | Description                                                                                                               | Details                                                                                                                                                                                                                     |
|----------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`./pipeline`](./pipeline)                         | Jupyter notebooks detailing the entire data processing, machine learning, and evaluation pipeline.                        | These notebooks detail every step in this workflow, from start to finish.                                                                                                                                                   |
| [`./preprocess`](./preprocess)                     | A set of Python CLI tools for preprocessing data assets.                                                                  | These tools help to reproject and threshold the ASO raster files, create vector footprints of raster data, tile the imagery for training, and other related tasks.                                                          |
| [`./model`](./model)                               | The implementation of the machine learning/computer vision techniques used by this project.                               | This work relies heavily on the [robosat.pink](https://github.com/datapink/robosat.pink) repository, which we've [forked](https://github.com/acannistra/robosat.pink) and modified extensively.                              |
| [`./sagemaker`](./sagemaker)                       | The infrastructure required to use [Amazon Sagemaker](https://aws.amazon.com/sagemaker/) to manage our ML training jobs.  | Sagemaker requires considerable configuration, including a Docker container. We build this container from this directory, which has a copy of the `./model` directory.                                                      |
| [`./experiments`](./experiments)                   | Configuration files that describe experiments used to assess the performance of this ML-based snow cover method.          | Our ML infrastructure uses "config files" to describe the inputs and other parameters to train the model effectively. We use these files to describe experiments that we perform, using different sets of ASO and imagery.  |
| [`./implementation-notes`](./implementation-notes) | Technical descriptions of the implementation considerations that went into this project.                                  | These are working documents, in raw Markdown format.                                                                                                                                                                        |
| [`./raster_utils`](./raster_utils)                 | Small utility functions for managing raster computations.                                                                 | Not much to see here.                                                                                                                                                                                                       |
| [`./environment`](./environment)                   | Raw Python environment configuration files.                                                                               | ⚠️ These emerge from `conda` and change often. Use sparingly. We preserve our environment via Docker, which should be used in this case (see the `./sagemaker` directory)                                                    |
| [`./analysis`](./analysis)                         | Jupyter notebooks that describe analyses about our snow mask product.                                                     | ⚠️ These are a work in progress and change frequently.                                                                                                                                                                       |

## Requirements
### Basic Requirements
The goal of this work is to provide a toolkit that is relatively easy to deploy for someone with **working knowledge** of the following tools:

* Python 3
* Jupyter notebooks
* Basic command-line tools

More specific requirements can be found in the [Infrastructure Deployment](#infrastructure-deployment) section below.

### Development Requirements

This free, open-source software depends on a good number of other free, open-source software packages that permit this work. To understand the inner workings of this project, you'll need familiarity with the following:

* [PyTorch](https://pytorch.org)
* [Tensorflow](https://www.tensorflow.org)
* [scikit-image](https://scikit-image.org)
* [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) / [s3fs](https://s3fs.readthedocs.io/en/latest/)
* [Geopandas](https://github.com/geopandas/geopandas) / [shapely](https://github.com/Toblerity/Shapely)
* [Rasterio](https://rasterio.readthedocs.io/en/stable/) / [rio-tiler](https://github.com/cogeotiff/rio-tiler)
* [mercantile](https://github.com/mapbox/mercantile) / [supermercado](https://github.com/mapbox/supermercado)
* [Amazon Sagemaker](https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html)


To build and manage our infrastructure, we use [Docker](https://www.docker.com) and [Terraform](https://www.terraform.io).


### Accounts and Data

<h4>
Amazon Web Services
<img align="right" src="https://d1.awsstatic.com/logos/aws-logo-lockups/poweredbyaws/PB_AWS_logo_RGB.61d334f1a1a427ea597afa54be359ca5a5aaad5f.png" style="float:right; padding: 5px" height=30>
</h4>



This project relies on cloud infrastructure from Amazon Web Services, which is a cloud services provider run by Amazon. AWS isn't the only provider in this space, but is the one we chose due to a combination of funding resources and familiarity. To run these tutorials and perform development tasks with this software, you'll need an AWS account. You can get one [here](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/).

<h4>Planet Labs
<img align="right" src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Planet_Labs_logo.svg/200px-Planet_Labs_logo.svg.png" style="float:right;" height=40>
</h4>

In order to access the imagery data from Planet Labs used to train our computer vision models and assess their performance, we rely on a relationship with collaborator [Dr. David Shean](https://dshean.github.io) in UW Civil and Environmental Engineering, who has access to Planet Labs data through a NASA Terrestrial Hydrology Program award.

If you're interested in getting access to Planet Labs imagery for research, check out the [Planet Education and Research Program](https://www.planet.com/markets/education-and-research/).

<h4>NASA Earthdata
<img align="right" src="./docs/nasa-logo.conv.png" style="float:right;" height=40>
</h4>

Finally, to gain access to the NASA/JPL Airborne Snow Observatory lidar-derived snow depth information, you need an account with NASA Earthdata. [Sign up here](https://urs.earthdata.nasa.gov/users/new).

## Infrastructure Deployment

To explore this work, and the tutorials herein, you'll need to deploy some cloud infrastructure to do so. This project uses [Docker](https://www.docker.com)and [Terraform](https://www.terraform.io) to manage and deploy consistent, reliable cloud infrastructure.

For detailed instructions on this process, view the [documentation](./deployment/).

To jump right to the guts of the deployment, here's our [Dockerfile](./sagemaker/Dockerfile) and Terraform [Resource Definition](./deployment/resources.tf).

## Tutorials

Through support from Earth Science Information Partners, we're happy to be able to provide thorough interactive tutorials for these tools and methods in the form of Jupyter notebooks. You can see these tutorials in the data pipeline folder [`./pipeline`](pipeline).

## Acknowledgements and Funding Sources

This work wouldn't be possible without the advice and support of Dr. Nicoleta Cristea, Dr. David Shean, Shashank Buhshan, and others.

We gratefully acknowledge financial support from the [Earth Science Innovation Partners Lab](https://www.esipfed.org), the [NASA Terrestrial Hydrology Program](https://neptune.gsfc.nasa.gov/index.php?section=19), the Planet Labs [Education and Research](https://www.planet.com/markets/education-and-research/) Program, and the [National Science Foundation](http://nsf.gov/).

<img src="http://www.bu.edu/cs/files/2016/09/NSF-Logo-1efvspb.png" height=70>
<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/500px-NASA_logo.svg.png" height=70">
<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Planet_Labs_logo.svg/200px-Planet_Labs_logo.svg.png" height=70>

## Original Proposal
To see the original resarch proposal for this project, now of date, view it [here](./original-proposal.md).
