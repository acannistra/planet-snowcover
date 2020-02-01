import os
import sys

from tempfile import mkdtemp

# os.environ["CURL_CA_BUNDLE"] = "/etc/ssl/certs/ca-certificates.crt"

import mercantile

import json

from shapely import geometry, ops

import s3fs
import boto3

from subprocess import Popen
import shlex

import click
import tqdm

sys.path.append("../../model/robosat_pink/")
from robosat_pink import datasets


def download_s3url(url, directory, s3fs):
    parsed = url[5:].split("/")
    bucket = parsed[0]
    key = os.path.join(*parsed[1:])
    slug = "-".join(parsed[1:])
    s3fs.download_file(bucket, key, os.path.join(directory, slug))


def getMaskTiles(mask_loc, destination, aws_profile):
    mask_loc = mask_loc if mask_loc.startswith("s3://") else "s3://" + mask_loc
    tiles = datasets.S3SlippyMapTiles(
        mask_loc, aws_profile=aws_profile, mode="multibands"
    ).tiles

    _session = boto3.Session(profile_name="esip")


@click.command()
@click.argument("prediction_path")
@click.argument("output_dir")
@click.option("--mask_loc", help="S3 bucket path containing mask tiles", required=True)
@click.option("--aws_profile")
def summarize(prediction_path, output_dir, mask_loc, aws_profile):
    """
    Collect relevant files to perform accuracy assessment for given prediction.

    Prediction path either must be in s3://<bucket>/<image-id>

    Included:
        * Prediction Tiles
        * Image Tiles
        * Mask Tiles

    """
    if ":" in prediction_path:
        imagepath = os.path.basename(prediction_path).replace(":", "/")
        print(imagepath)
    else:
        print("pred needs to contain image dir in path ")
        exit(1)

    ## ASO Mask Tiles
    mask_name = os.path.basename(mask_loc)
    mask_loc = mask_loc if mask_loc.startswith("s3://") else "s3://" + mask_loc
    mask_tiles = datasets.S3SlippyMapTiles(
        mask_loc, aws_profile=aws_profile, mode="multibands"
    ).tiles

    ## Prediction Tiles
    prediction_path = (
        prediction_path
        if prediction_path.startswith("s3://")
        else "s3://" + prediction_path
    )
    pred_tiles = datasets.S3SlippyMapTiles(
        prediction_path, mode="multibands", aws_profile=aws_profile, ext="tif"
    ).tiles

    ## Image Tiles
    imagepath = imagepath if imagepath.startswith("s3://") else "s3://" + imagepath
    image_tiles = datasets.S3SlippyMapTiles(
        imagepath, mode="multibands", aws_profile=aws_profile
    ).tiles

    mask_ids, mask_tile_ids, mask_paths = zip(*mask_tiles)
    pred_ids, pred_tile_ids, pred_paths = zip(*pred_tiles)

    print(len(pred_tile_ids), len(mask_tile_ids))

    tile_overlap = set(pred_tile_ids).intersection(set(mask_tile_ids))

    assert len(tile_overlap) > 0, "No overlapping tiles. Double-check mask path."

    # Filter all tiles by overlap
    mask_tiles = [_ for _ in mask_tiles if _[1] in tile_overlap]
    pred_tiles = [_ for _ in pred_tiles if _[1] in tile_overlap]
    image_tiles = [_ for _ in image_tiles if _[1] in tile_overlap]

    # create dir
    workdir = os.path.join(output_dir, prediction_path.replace("/", ":"))
    os.makedirs(workdir, exist_ok=True)
    maskdir = os.path.join(workdir, "mask")
    os.makedirs(maskdir, exist_ok=True)
    preddir = os.path.join(workdir, "preds")
    os.makedirs(preddir, exist_ok=True)

    ## Create data extent polygon
    pred_mask = ops.cascaded_union(
        [geometry.Polygon.from_bounds(*mercantile.bounds(t_i)) for t_i in tile_overlap]
    )
    with open(os.path.join(workdir, "data-mask.geojson"), "w") as f:
        f.write((json.dumps(geometry.mapping(pred_mask))))

    ## Download pertinent tiles
    s3 = boto3.Session(profile_name=aws_profile).client("s3")
    for p_t, i_t in tqdm.tqdm(zip(pred_tiles, image_tiles), total=len(tile_overlap)):
        tile = p_t[1]
        masktileloc = "{}/{}/{}/{}.tif".format(mask_loc, tile.z, tile.x, tile.y)

        try:
            download_s3url(p_t[2], preddir, s3)
        except Exception as e:
            print("Download failed {} ({})".format(p_t[2], e))
        try:
            download_s3url(masktileloc, maskdir, s3)
        except Exception as e:
            print("Download failed {} ({})".format(masktileloc, e))

    ## Merge Mask tiles and Predction Tiles into single tifs
    MERGE_CMD = "gdal_merge.py -ot 'Int16' -co 'COMPRESS=LZW' -o {dir}/{fname}.tif $(find {dir} -name '*.tif')"

    _p = Popen(
        MERGE_CMD.format(dir=maskdir, fname=os.path.basename(mask_loc)),
        shell=True
    ).communicate()
    _p = Popen(
        MERGE_CMD.format(dir=preddir, fname=os.path.basename(imagepath)),
        shell=True
    ).communicate()


if __name__ == "__main__":
    summarize()
