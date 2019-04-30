# Planet SCA (<small>snow-covered area</small>) Cloud Infrastructure Design

**Tony Cannistra**, April 2019

To assess the utility of [Planet Labs](www.planet.com)' daily 3m 4-band imagery product ([`PlanetScope`](https://assets.planet.com/docs/Planet_Combined_Imagery_Product_Specs_letter_screen.pdf)) in assessing snow-covered area, we avail ourselves of *three* primary cloud technologies: storage, hosted development environments, and GPUs. We explain each of these below, in the context of the primary concerns of this project: data processing and model training. (For a brief overview of the software architecture supported by this infrastructure, see here (TODO)).



## Cloud Storage (AWS S3)

All data used to complete this project exist within object storage on Amazon S3. Three concerns motivated the use of cloud storage as the repository for the necessary data in this project: development flexibility, imagery acquisition, and data volume.

### Development Flexibility

The storage of data in an object storage solution (like S3) allows for a variety of clients to access it. Each of the three phases of this project (image acquisition, processing, and model training) are completed on different sets of computational infrastructure, thereby making the flexible nature of object storage the natural choice. This avoids unnecessary data copying procedures, and only requires relatively minor infrastructural considerations in development. The "killer feature" here is that any software developed based on s3 object storage can be run on any infrastructure with access to the S3 buckets, which greatly simplifies development.

### Imagery Acquisition

Planet Labs has a robust [API](https://developers.planet.com/docs/orders/reference/#) which abstracts complex image operations including imagery ordering, image subsetting, and band math, among others. Planet can deliver final data products from this compute API directly to cloud storage, which simplifies the infrastructure required to process the data.

These data are also either delivered as, or are converted to, the [Cloud Optimized GeoTIFF](https://www.cogeo.org/) storage format. This format allows for efficient cloud-based processing workflows by permitting HTTP Range requests, allowing partial reads of large files on the cloud. 

### Data Volume

Though the initial data volume used to train our models has been relatively small (< 10 GB), we are currently in a scale-up period where we hope to use all available ground-truth and imagery collections over a single year for a single watershed to create a robust proof-of-concept for this model. Data volumes for this task range well over 100GB, which, while still very tractable in a local computing environment, severely limits this distributed development model which we've used to create the software required for this project. Copying 100GB of data from one endpoint to another isn't terribly exciting, but s3 availability solves this problem.

### A Note on Bandwidth

Of course, in order to perform an analysis upon these imagery data, it must be somehow loaded into working memory on some computer. This requires the transfer of data out of object storage over a network connection, which has the potential to introduce both latency and financial cost. However, because of the data architecture (described elsewhere) which relies on small (< 4MB) units ("tiles") of imagery, data download times are small and scale linearly with the size of the computational task. Furthermore, since these computations are occurring within the same AWS "Region", bandwidth is free. (Bandwidth from AWS to the outside internet is ~$0.09/GB, depending on total data volume / month).


## Hosted Development Environments

This project makes use of commodity EC2 instances for hosting Jupyterlab, where much of the software development takes place. We experimented with xarray and dask via a Kubernetes cluster, but this approach was overkill for our data volume.

## GPU instances

To train the large neural network required for this project, we use GPU-enabled instances from AWS EC2. This service allows for much more efficient computation than traditional cpu-based instances. We use `PyTorch` for the development of models which can leverage GPU-based training.

## Resources/Related Tools

* [`s3fs`](https://s3fs.readthedocs.io/en/latest/): Python file system abstraction for s3
* [`boto3`](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html): AWS SDK for Python
* [AWS GPU Instance Pricing](https://aws.amazon.com/ec2/instance-types/p2/)
