# Planet SCA ML Architecture Design
**Tony Cannistra, August 2019**

As with most neural network-based machine learning projects, a significant amount of compute power is required to efficiently train these very large models. In particular, to train the [`robosat.pink`/TernausNetV2](https://github.com/acannistra/robosat.pink) model, a computer with at least 8 CPUs and 60GB of RAM is required. However, since the computation required to train a neural network is easily optimized via the use of GPUs, we can leverage these resources to reduce the CPU burden and processing time. 

I assessed two options for the training of this model, and settled on one. The first option I investigated was the simplest: configuring  a GPU-enabled EC2 instance (`p2.xlarge`, for example) and manually instantiating each training experiment via an SSH command line. This approach, while effective, was cumbersome and prone to errors. 

The final approach I selected was the use of [Amazon SageMaker](https://aws.amazon.com/sagemaker) – a managed machine learning training and evaluation service – to manage model training. I describe this approach below. 

## SageMaker Configuration
My initial aversion to Sagemaker-based training was the configuration burden required to use it. This section will describe some of this configuration. I won't try to describe the Sagemaker workflow entirely, as there are [other resources](https://docs.aws.amazon.com/sagemaker/latest/dg/how-it-works-training.html) available for that. However, I will describe the high-level workflow enough to understand the configuration process. All files mentioned during this process are available in the [`/sagemaker`](../../sagemaker) directory at the root of this repository. 

### Sagemaker Overview
In short, the SageMaker training process is as follows:

1. Define and test a training algorithm and compute environment (via Docker). 
1. Upload resulting Docker container to Amazon Elastic Container Registry (ECR)
1. Deploy training data to S3.
1. Configure a "Training Job" via Amazon SageMaker console or API, specifying training configuration and compute hardware.  
1. SageMaker executes training job by deploying the above Docker container to automatically-provisioned compute hardware and executing training routine within Docker container.
1. Upload model artifacts to S3. 

**Important Note**: if you spend any time reading the SageMaker documentation, you'll see the docs refer to "training and validation data in S3." One of the intended features of SageMaker is the built-in ability to copy training data stored in S3 directly local to the compute environment where training is taking place, removing one layer of complexity from the training process. **However**, because we have highly-structured training data in S3 for this project (image tiles, see [`data-architecture.md`](./data-architecture.md)), we don't take advantage of this functionality. Instead, we use the S3-copying functionality to copy a *configuration file* to the local compute environment, which is then *read by the training code* ([`robosat.pink/robosat_pink/tools/train.py`](https://github.com/acannistra/robosat.pink/blob/master/robosat_pink/tools/train.py#L64)). This allows us both to easily configure each training run (by uploading a configuration file to S3 and specifying it in the Training Job configuration) and still leverage S3 object storage. 

### Docker Configuration
Sagemaker's training process uses a Docker container to encapsulate the software and compute environment necessary to complete the training process. To do this, we constructed a [`Dockerfile`](https://github.com/acannistra/planet-snowcover/blob/master/sagemaker/Dockerfile) which describes the compute environment required to run the training code. At a high-level, this Dockerfile:

* Is based in the `ubuntu:16.04` image
* Installs Python3.6 and `pip` from `apt`
* Installs `conda` and uses [`pytorch_p36.yml`](https://github.com/acannistra/planet-snowcover/blob/master/environment/pytorch_p36.yml) to update the root conda environment. 
* Copies the `/model` code into the SageMaker specified place in the image. 
* Copies `./start.sh` from the `/sagemaker` directory into the image, which allows the Docker container to implement the commands required by SageMaker. 

For a complete description of this environment, consult the Dockerfile. 

We use Amazon ECR to host the repository, as required by SageMaker. It's located at `675906086666.dkr.ecr.us-west-2.amazonaws.com/planet-snowcover`, which isn't public. 

### SageMaker Algorithm Configuration 

We have to create an algorithm configuration for SageMaker to be able to use our algorithm when we create a Training Job. This simply allows us to specify the container location (listed above) and the "input channels." SageMaker uses S3 to store model data and artifacts – an "Input Channel" is typically how one would tell SageMaker where the *training data* lives so that it can copy it into the container, but we use it to copy a *configuration file* to the container. We name the input channel `config`. 

The algorithm we've configured is at `arn:aws:sagemaker:us-west-2:675906086666:algorithm/planet-snowcover-cnn-copy-08-05`, and is not publicly accessible. (AWS has strict validation requirements to listing algorithms publicly, which we won't implement for this project. You can create this algorithm yourself quite easily, described above). 

