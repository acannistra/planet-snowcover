from os import path
import sys

import click
import subprocess
import toml
import s3fs
import boto3

from shutil import copyfile

import pprint

import tempfile

from glob import glob

PREDICT_COMMAND = "cd {rsp}; ./rsp predict --create_tif --checkpoint {checkpoint} --aws_profile {aws_profile} --config {config} --tile_ids {ids} {outputloc}"

S3_COPY_COMMAND = "aws s3 cp --profile {aws_profile} --recursive {local} {remote}"


@click.command()
@click.argument("config")
@click.argument("model_output_dir")
@click.option("--test_only", is_flag=True)
@click.option("--test_location")
@click.option("--aws_profile", required=True)
@click.option("--checkpoint_name", "-c", default="checkpoint-00050-of-00050.pth")
@click.option("--other_checkpoint", help="Full path to separate checkpoint.")
@click.option(
    "--robosat_pink", "--rsp", "rsp", default="~/planet-snowcover/model/robosat_pink"
)
@click.option("--prediction_output", "-o", "prediction_output")
def run_prediction(
    config,
    model_output_dir,
    test_only,
    test_location,
    aws_profile,
    checkpoint_name,
    other_checkpoint,
    rsp,
    prediction_output,
):
    """
    Runs model specified using <model_output_dir>/<checkpoint_name> using robosat_pink (located at <rsp>).

    Produces predictions for images specified in <config> in s3 bucket (either <model_output_dir> or <prediction_output>) with
    diretory format <config_name>:<image_path>. Optionally uses test_ids.txt in <model_output_dir> to limit prediction tiles.

    """
    assert path.exists(
        path.expanduser(path.join(rsp, "rsp"))
    ), "Robosat code not found at {}".format(rsp)
    print("Found robosat code at {}".format(rsp))
    config_id = path.splitext(path.basename(config))[0]

    temp_dir = tempfile.TemporaryDirectory(prefix=config_id)
    fs = s3fs.S3FileSystem(session=boto3.Session(profile_name=aws_profile))

    # Load TEST ids for prediction.
    test_ids = None
    if test_only:
        if test_location:
            print("Using test ids at {}".format(test_location))
            if test_location.startswith("s3://"):
                fs.get(test_location, path.join(temp_dir.name, "test_ids.txt"))
            else:
                # local file
                copyfile(test_location, path.join(temp_dir.name, "test_ids.txt"))
        else:
            # assume intended test_ids.txt is within <model_output_dir>
            print("Using test_ids.txt within {}".format(model_output_dir))
            fs.get(
                path.join(model_output_dir, "test_ids.txt"),
                path.join(temp_dir.name, "test_ids.txt"),
            )

    assert path.exists(path.join(temp_dir.name, "test_ids.txt"))

    prediction_output_loc = path.join(temp_dir.name, config_id)

    checkpoint = path.join(model_output_dir, checkpoint_name) if other_checkpoint is None else other_checkpoint

    predict_command = PREDICT_COMMAND.format(
        rsp=rsp,
        checkpoint=checkpoint,
        aws_profile=aws_profile,
        config=path.abspath(config),
        ids=path.join(temp_dir.name, "test_ids.txt"),
        outputloc=prediction_output_loc,
    )

    pp = pprint.PrettyPrinter(indent=4)

    print("Executing prediction command:")
    pp.pprint(predict_command)

    proc = subprocess.Popen(predict_command, shell=True).communicate()

    s3_command = S3_COPY_COMMAND.format(
        aws_profile=aws_profile,
        local=prediction_output_loc,
        remote=prediction_output if prediction_output else model_output_dir,
    )

    proc = subprocess.Popen(s3_command, shell=True).communicate()


if __name__ == "__main__":
    run_prediction()
