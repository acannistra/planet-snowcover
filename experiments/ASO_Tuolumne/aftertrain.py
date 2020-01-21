import click
import boto3
import s3fs
from datetime import datetime 
from os import path, mkdir
import tarfile
from tempfile import mkdtemp, TemporaryDirectory
from subprocess import Popen, PIPE

@click.command()
@click.argument('result_path')
@click.option("--aws_profile", "-p", "aws_profile", required=True)
@click.option("--aws_region", "-r", required=True)
@click.option("--output", '-o', "output_dir", required=False)
def process_training_output(result_path, aws_profile, aws_region, output_dir):
    sess = boto3.Session(profile_name=aws_profile, region_name=aws_region)
    fs = s3fs.S3FileSystem(session = sess)
    
    assert "output" in [path.basename(p) for p in fs.ls(result_path)], "Output not found in {}".format(result_path)

    tmpdir = TemporaryDirectory(prefix=result_path.replace("/", "_"))
        
    print("Downloading trained model...")
#     fs.get(path.join(result_path, 'output', 'model.tar.gz'), path.join(tmpdir.name, "model.tar.gz"))
    p = Popen(['aws', 's3', '--profile', aws_profile, 'cp', 
               path.join(result_path, 'output', 'model.tar.gz'), 
               path.join(tmpdir.name, 'model.tar.gz')], stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate()

    
    print("Extracting trained model...")
    members = [
        "checkpoint-00050-of-00050.pth", 
        "test_ids.txt", 
        "train_ids.txt"
    ]
    tarball = tarfile.open(path.join(tmpdir.name, "model.tar.gz"), mode='r:gz')

    # make output_dir if needed
    if output_dir and not path.exists(output_dir):
        mkdir(output_dir)
        
    [tarball.extract(file, path=output_dir if output_dir else tmpdir.name) for file in members]
    
    print("Uploading back to S3...")
    [fs.put(path.join(tmpdir.name, file),
            path.join(result_path, file)) for file in members]
    
   
    print("Cleaning up ...")
    tmpdir.cleanup()
    
    
if __name__ == "__main__":
    process_training_output()