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

### Docker Configuration
Sagemaker's training process uses a Docker container to encapsulate the software and compute environment necessary to complete the training process.

