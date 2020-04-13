import os
import sys
import logging

import click


import rasterio as rio
from rasterio.warp import calculate_default_transform, reproject
from rasterio.io import MemoryFile
from rasterio.enums import Resampling
from rasterio.mask import mask as rio_mask
from rasterio.vrt import WarpedVRT

import numpy as np

from tabulate import tabulate

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from glob import glob

from shapely.geometry import shape

from sklearn import metrics

import json

@click.group()
def compare():
    pass

def reproject_like(this, reproject_this):
    dst = MemoryFile()

    d_transform, d_width, d_height = calculate_default_transform(
        reproject_this.crs, this.crs, reproject_this.width, reproject_this.height, *reproject_this.bounds
    )

    dst_profile = reproject_this.profile.copy()
    dst_profile.update(
        {
            "driver": "GTiff",
            "crs": this.crs,
            "transform": d_transform,
            "width": d_width,
            "height": d_height,
        }
    )
    #
    with rio.open(dst, 'w', **dst_profile) as dst_file:
        reproject(
            source=reproject_this.read(1),
            destination=rio.band(dst_file,1),
            src_transform=reproject_this.transform,
            src_crs=reproject_this.crs,
            dst_transform=d_transform,
            dst_crs=this.crs,
            resampling=Resampling.bilinear
        )

    dst.seek(0)
    return dst.open()


def reproject_like_vrt(this, reproject_this):
    new_transform, new_width, new_height = calculate_default_transform(
        reproject_this.crs, this.crs,
        reproject_this.width, reproject_this.height,
        *reproject_this.bounds
    )

    prof = this.profile.copy()
    prof.update({
        'resampling': Resampling.nearest,
        'crs' : this.crs,
        'transform': new_transform,
        'height' : new_height,
        'width' : new_width
    })

    return WarpedVRT(reproject_this, **prof)


def clip_vrt(this_vrt, region):
    this_masked, this_transform = rio_mask(this_vrt, region)

    prof = this_vrt.profile.copy()
    prof.update({
        'transform': this_transform,
        'height': this_masked.shape[0],
        'width' : this_masked.shape[1]
    })

    return WarpedVRT(this_vrt, **prof)

    # dst = MemoryFile()
    # dst_profile = this.profile.copy()
    # dst_profile.update({
    #     'height' : this_masked.shape[1],
    #     'width' : this_masked.shape[2],
    #     'transform' : this_transform
    # })
    #
    # with rio.open('testclip.tif', 'w', **dst_profile) as dst_file:
    #     dst_file.write(this_masked)
    #
    # dst.seek(0)
    # return dst.open()


def compute_metrics(true, pred):
    print(true.shape, pred.shape)
    assert true.shape == pred.shape, "Masks and predictions are different shapes. Are you sure they're in the same CRS/extent?"

    compare = (true, pred)

    balanced_acc = metrics.balanced_accuracy_score(*compare)
    prfs = metrics.precision_recall_fscore_support(*compare, average='binary')

    these_metrics = {
        "balanced_accuracy" : balanced_acc,
        "precision": prfs[0],
        "recall": prfs[1],
        "f_score": prfs[2]
    }

    return these_metrics


@compare.command()
@click.argument('directory')
@click.option("--mask_dir", help="Name for ASO directory [default: 'mask']", default='mask')
@click.option('--s2', help="Sentinel 2 directory [default: sentinel-2]", default='sentinel-2')
@click.option("--no_clip", help="specify if no clipping of NDSI is needed.", is_flag=True)
def sentinel(directory, mask_dir, s2, no_clip):
    """
    Compare ASO in <directory> to Sentinel-2 NDSI found in <directory>.

    Looks for *merged.tif ASO files and sentinel-2 directory.
    """
    dirfiles = os.listdir(directory)
    assert mask_dir in dirfiles, f"Mask directory '{mask_dir}' not found in {directory}"
    assert s2 in dirfiles, f"Sentinel 2 directory '{s2}' not found in {directory}"

    mask_file = glob(os.path.join(directory, mask_dir, "*merged*.tif"))[0]
    mask = rio.open(mask_file)

    if not no_clip:
        data_region = shape(json.load(open(glob(os.path.join(directory, "data-mask.geojson"))[0])))


    s2_files = glob(os.path.join(directory, s2, "*/NDSI.tif"))
    if len(s2_files) > 1:
        tabulate(s2_files)
        image_iloc = int(input("More than one NDSI found. Choose [0-{}]: ".format(len(s2_files) - 1)))
        s2_file = s2_files[image_iloc]
    else:
        s2_file = s2_files[0]

    print(f"NDSI: {s2_file}")
    print(f"Mask: {mask_file}")
    ndsi = rio.open(s2_file)

    try:
        assert mask.crs == ndsi.crs, f"CRS of mask and NDSI are different. [{mask.crs['init']}, {ndsi.crs['init']}]"
    except AssertionError as e:
        print(e)
        print("Reprojecting...")
        ndsi = reproject_like_vrt(mask, ndsi)


    print(ndsi)
    # if not no_clip:
    #     print("Clipping.")
    #     ndsi = clip_vrtcm(ndsi, data_region)



    mask_data = mask.read(1)
    # Resample NDSI to match mask
    ndsi_data = ndsi.read(1)

    print(mask_data.shape, ndsi_data.shape)
    sys.exit(1)

    try:
        aso_mask = np.where(mask_data != mask.nodata)
        ndsi_mask = np.where(ndsi_data != ndsi.nodata)
        mask_data = mask_data[aso_mask]
        ndsi_data = ndsi_data[ndsi_mask]
    except Exception as e:
        print("Error filtering nodata. Do input data files have nodata attribute set? [{}]".format(e))
        sys.exit(1)

    print(len(np.unique(mask_data)))
    print(len(np.unique(ndsi_data)))
    these_metrics = compute_metrics(mask_data, ndsi_data)

    results = {
        "mask": mask_file,
        "ndsi": s2_file,
        "metrics" : these_metrics
    }

    print(results)
    outfile = os.path.join(directory, "sentinel-2_metrics.json")
    with open(outfile, 'w') as o:
        json.dump(results, o)


@compare.command()
@click.argument("directory")
@click.option("--plot", help="output plot to directory", is_flag=True)
@click.option("--mask_dir", help="Name for ASO directory [default: 'mask']", default='mask')
def prediction(directory, plot, mask_dir):
    """
    Compare ASO in <directory> to predictions found in <directory>.

    Looks for *merged.tif files.
    """

    dirfiles = os.listdir(directory)
    assert mask_dir in dirfiles, f"Mask directory '{mask_dir}' not found in {directory}"
    assert "preds" in dirfiles, f"Prediction directory not found in {directory}"

    mask_file = glob(os.path.join(directory, mask_dir, "*merged*.tif"))[0]
    mask = rio.open(mask_file)

    preds_file = glob(os.path.join(directory, "preds", "*merged*.tif"))[0]
    preds = rio.open(preds_file)

    mask_data = mask.read(1).flatten()
    pred_data = preds.read(1).flatten()
    # remove nodata
    try:
        mask_data = mask_data[np.where(mask_data != mask.nodata)]
        pred_data = pred_data[np.where(pred_data != preds.nodata)]
    except Exception as e:
        print("Error filtering nodata. Do input data files have nodata attribute set? [{}]".format(e))
        sys.exit(1)

    metrics = compute_metrics(mask_data, pred_data)

    results = {
        "mask": mask_file,
        "preds": preds_file,
        "metrics" : metrics
    }
    print(results)
    outfile = os.path.join(directory, "aso_metrics.json")
    with open(outfile, 'w') as o:
        json.dump(results, o)




if __name__ == '__main__':
    compare()
