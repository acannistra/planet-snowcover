import click
import sagemaker
import boto3
import toml
import s3fs
from datetime import datetime
from os import path
from pprint import pprint
import sys

CONSOLE_JOB_URL = "https://{region}.console.aws.amazon.com/sagemaker/home?region={region}#/jobs/{job}"

def build_estimator(session, prefix, sagemaker_image, sage_role_arn, output_bucket):
    sage_sess = sagemaker.Session(boto_session=session)
    e = sagemaker.estimator.Estimator(sagemaker_image, 
                                      sage_role_arn, 1, "ml.p2.xlarge", 
                                      train_volume_size = 150,
                                      output_path = "s3://" + output_bucket,
                                      sagemaker_session = sage_sess, 
                                      base_job_name = prefix)
    return(e)

    

@click.command()
@click.argument('config')
@click.option("--image", "-i", "sagemaker_image", required=True, type=str)
@click.option("--sage_role_arn", "-r", required=True, type=str)
@click.option("--aws_profile", "-p", "aws_profile", required=True)
@click.option("--aws_region", default="us-west-2")
@click.option("--config_bucket", "-cb", "config_bucket", required=True)
@click.option("--output_bucket", "-b", "output_bucket", required=True)
@click.option("--max_runtime", "max_runtime", required=True, default=(60 * 60 * 10)) # 10 hours
def sage_train(config, sagemaker_image, sage_role_arn, aws_profile, aws_region, config_bucket, output_bucket, max_runtime):
    sess = boto3.Session(profile_name=aws_profile, region_name=aws_region)
    fs = s3fs.S3FileSystem(session = sess)
    
    print("\nConfig File: {}".format(config))
    pprint(toml.load(open(config)), indent = 5)

    # upload config to bucket 
    ans = input("Upload {} to {}? [y/n]: ".format(config, config_bucket))
    
    if ans.lower() != "y":
        sys.exit(1)
    
    fs.put(config, "{}/{}".format(config_bucket, path.basename(config)))
    config_location = "s3://{}/{}".format(config_bucket, path.basename(config))
    print("Uploaded {} to {}.".format(config, config_location))
    
    # create estimator 
    job_prefix = path.splitext(path.basename(config))[0]
    e = build_estimator(sess, job_prefix, sagemaker_image, sage_role_arn, output_bucket)
    
    ans = input("START SAGEMAKER TRAINING JOB? [y/n]: ")
    if ans.lower() != "y":
        print("Aborted.")
        sys.exit(1)
        
    e.fit({
        'config': config_location
    }, wait=False)
    
    
    
    job_url = CONSOLE_JOB_URL.format(region = aws_region, job = e.latest_training_job.name)
    print("Job started, visit {} for more and to stop job.".format(job_url))
    
    print("Live logs (exit will not stop job.)")
    
    sage_sess = sagemaker.Session(boto_session=sess)
    sage_sess.logs_for_job(e.latest_training_job.job_name, wait=True) 
    
    
    
if __name__ == "__main__":
    sage_train()