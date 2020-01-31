import sys
from os import path, environ, makedirs

from glob import glob

import click

import fiona
from shapely.geometry import shape

from pandas import to_datetime
from pandas.io.json import json_normalize

from tabulate import tabulate

from datetime import datetime, timedelta

from cmr import GranuleQuery

from subprocess import Popen
import shlex

MODIS_SNOW_CMR_SHORT_NAME = "MOD10A1"


@click.group()
def modis():
    pass


@modis.command()
@click.argument("destination")
@click.option(
    "--image_date",
    "date",
    help="Date of image collection.",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    required=True,
)
@click.option("--search_window", help="Imagery search window.", default=2)
@click.option(
    "--footprint", help="Data footprint geojson (within <destination>!).", required=True
)
@click.option("--chooser", "choose", help="show chooser", is_flag=True)
@click.option("--clip", help="clip MODIS to footprint", is_flag=True)
@click.option("--reproject", help="reproject MODIS clipped to projection")
def get_modis(destination, date, search_window, footprint, choose, clip, reproject):
    """
    Retrieves MODIS scenes.

    Scenes must entirely contain <footprint> within date +/- search_window.
    """
    workdir = path.join(destination, "modis")
    makedirs(workdir, exist_ok=True)

    footprint_path = path.join(destination, footprint)
    searchFootprint = shape(fiona.open(footprint_path)[0]["geometry"])

    date_window = timedelta(days=search_window)
    date_range = (date - date_window, date + date_window)

    cmrAPI = GranuleQuery()

    results = (
        cmrAPI.short_name(MODIS_SNOW_CMR_SHORT_NAME)
        .bounding_box(*searchFootprint.bounds)
        .temporal(*date_range)
        .get()
    )

    results = json_normalize(results)
    print(results["time_start"].iloc[0])
    print(date)
    results["time_start"] = to_datetime(results["time_start"]).dt.tz_localize(None)

    results["timedeltas"] = (date - results.time_start).abs()
    results = results.sort_values(by="timedeltas", ascending=True)
    results["browse"] = [
        [_i["href"] for _i in image_links if _i.get("title", "") == "(BROWSE)"][0]
        for image_links in results.links
    ]
    print(results.iloc[0].links)

    image_iloc = 0
    if choose:
        print(
            tabulate(
                results[
                    ["cloud_cover", "day_night_flag", "timedeltas", "browse"]
                ].reset_index(drop=True),
                headers="keys",
            )
        )
        image_iloc = int(input("Choose image ID [0-{}]: ".format(len(results) - 1)))

    image_url = results.iloc[image_iloc].links[0]["href"]
    MODIS_DL_COMMAND = (
        "wget "
        "--http-user=$EARTHDATA_USERNAME "
        "--http-password=$EARTHDATA_PASSWORD "
        "--no-check-certificate --auth-no-challenge "
        '-r --reject "index.html*" -np -e robots=off -nH -nd '
        "--directory-prefix={destination} "
        "{image_url}".format(destination=workdir, image_url=image_url)
    )

    _sh = Popen(MODIS_DL_COMMAND, shell=True).communicate()

    ## have to do some gdal magic with MODIS data.
    ## 1) turn it into a TIFF with the right projection.
    MODISfile = glob(path.join(workdir, "MOD10A1*.hdf*"))[0]
    output_file = path.join(workdir, "MODIS_reproj.tif")

    MODIS_CONVERT_COMMAND = (
        "gdalwarp "
        "HDF4_EOS:EOS_GRID:{path}:MOD_Grid_Snow_500m:NDSI_Snow_Cover "
        "-cutline {footprint} -crop_to_cutline -dstnodata 9999 "
        "-t_srs {projection} -r cubic "
        "-s_srs '+proj=sinu +R=6371007.181 +nadgrids=@null +wktext' "
        "{output_tif} ".format(
            path=MODISfile,
            footprint=footprint_path,
            projection=reproject,
            output_tif=output_file,
        )
    )

    _sh = Popen(MODIS_CONVERT_COMMAND, shell=True).communicate()

    print(MODISfile, output_file)


if __name__ == "__main__":
    modis()
