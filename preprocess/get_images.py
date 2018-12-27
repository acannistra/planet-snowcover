import argparse
import unittest

from datetime import datetime, timedelta
from dateutil.parser import isoparse

from shapely.geometry import shape
from json import loads

from planet_utils.search import SimpleSearch
from planet_utils.download import CroppedDownload

from os import makedirs, path

from multiprocessing import Pool as ThreadPool
from functools import partial

import pandas as pd
import geopandas as gpd

import subprocess


from yaspin import yaspin
SUCCESS = "✔"
FAIL = "💥 "

DESCRIPTION = """
Consumes geojson footprint, along with date and optional date range arguments and queries image search API to identify download candidates.

Selects candidates and uses Planet Clips API to download imagery within bounds of data footprint. Imagery with ID = `ID` is unzipped and placed also into output_dir.

"""

class TestGetImages(unittest.TestCase):
    pass #ha

def add_parser(subparser):
    parser = subparser.add_parser(
        "get_images", help = "Fetch images for given footprint and date.",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--footprint", help="desired imagery footprint.",
                        required = True)

    parser.add_argument("--date", help="date range centerpoint (YYYY/MM/DD)",
                        required = True,
                        type = isoparse)

    parser.add_argument("--date_range",
                        help="number of days on either side of  centerpoint to search for imagery",
                        default = 10,
                        type = int)

    parser.add_argument("output_dir",
                        help="imagery output directory. (AWS S3 and GCP GS compatible).")

    parser.add_argument("--max_images",
                        help="maximum number of images to download. If any of max_overlap, nearest_date, or max_cloud_cover are set, those will be used to select images, otherwise images will be returned in order of Planet API result.",
                        type = int)

    parser.add_argument("--max_overlap",
                        help="choose images based on maximum overlap to input geometry",
                        action = 'store_true')

    parser.add_argument("--nearest_date",
                        help="choose images based on closeness of image to date given.",
                        action = 'store_true')

    parser.add_argument("--max_cloud_cover",
                        help="remove images with cloud cover greater than a value.",
                        type=float)

    parser.add_argument("--aws_profile",
                        help = "AWS CLI Profile to use if s3:// url is given.",
                        type = str)

    parser.add_argument("--unzip",
                        help = "Unzips .zip archives from Planet API into output_dir",
                        action = 'store_true')


    parser.set_defaults(func = main)

def _search(footprint, start_date, end_date, dry=False):
    s = SimpleSearch(footprint, start_date, end_date, dry, quiet=True)

    return(s.query())

def _select_candidates(images, max_images = None, max_overlap = None, nearest_date = None, max_cloud_cover = None):
    """
    chooses at most max_images (None => choose all), respecting max_overlap (True = sorts by overlap with input geometry before choosing), nearest_date (True = sorts by abs(acquire_date - args.date) before choosing), and max_cloud_cover (float (0-1) -> removes images with cloud cover > max_cloud_cover).

    """
    if max_cloud_cover is not None:
        images['cloud_cover'] = [r['cloud_cover'] for r in images.properties.values]
        images = images[images.cloud_cover <= max_cloud_cover]

    if max_images is None:
        return images

    if max_overlap:
        images = images.sort_values('overlap', ascending = False)

    if nearest_date:
        images = images.sort_values('datediff')

    if max_overlap and nearest_date:
        images = images.sort_values(['overlap', 'datediff'],
                                    ascending = [False, True])

    if max_images is not None:
        return(images.head(max_images))

    return(images)

def _download_images(images, geometry, output_dir, aws_profile):
    geom_overlaps = [g.intersection(geometry).envelope for g in images.geometry.values] # adding envelope because original geom too large.

    downloader = CroppedDownload(0, geom_overlaps, images['id'].values, output_dir, aws_profile)

    filenames = downloader.run()
    return(filenames)


def _process_zip(zipFile, output_dir, aws_profile = None):
    """
    Unzip Planet image archive to output_dir (if s3:// can provide aws_profile)
    """
    from zipfile import ZipFile
    from smart_open import smart_open
    from fnmatch import fnmatch

    f = ZipFile(zipFile)
    files = []
    for f_i in f.namelist():
        f_iter = f.open(f_i)
        with smart_open(path.join(output_dir, f_i), 'wb') as w:
            for line in f_iter:
                w.write(line)
        files.append(f_i)

    return(files)




def get_images(geometry, date, date_range, output_dir, max_images = None,
               max_overlap = None, nearest_date = None, max_cloud_cover = None, aws_profile=None):

    center_date = date
    start_date = center_date - timedelta(days = date_range)
    end_date = center_date + timedelta(days = date_range)

    search_hull = geometry.convex_hull
    with yaspin(text="searching Planet API.", color="red") as spinner:
        images = _search(search_hull, start_date, end_date)
        spinner.text = "found {} images.".format(len(images))
        spinner.ok(SUCCESS)


    # supplement in order to _select_candidates
    images = gpd.GeoDataFrame(images, geometry = [shape(g) for g in images.geometry.values])

    images['datediff'] = [abs(pd.to_datetime(r['acquired']) - center_date) for r in images.properties.values]

    images['overlap'] = [g.intersection(geometry).area for g in images.geometry.values]

    images = _select_candidates(images, max_images, max_overlap, nearest_date, max_cloud_cover)

    filenames = _download_images(images, geometry, output_dir, aws_profile)

    return(filenames)




def main(args):
    makedirs(args.output_dir, exist_ok = True)

    gdf = gpd.read_file(args.footprint)
    geometry = gdf.geometry.values[0]

    filenames = get_images(geometry, args.date, args.date_range, args.output_dir, args.max_images, args.max_overlap, args.nearest_date, args.max_cloud_cover, args.aws_profile)

    if args.unzip:
        with yaspin(text="unzipping images...") as s:
            tp = ThreadPool()
            __unzipper = partial(_process_zip, output_dir = args.output_dir, aws_profile = args.aws_profile)
            unzipped = list(tp.map(__unzipper, filenames))
            s.ok(SUCCESS)

    [print(i) for i in unzipped]
    return(0)
