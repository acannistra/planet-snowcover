import sys
from os import path, environ, makedirs

import click

from sentinelsat.sentinel import SentinelAPI, read_geojson, geojson_to_wkt
from sentinelhub import AwsTileRequest, AwsTile, DataSource
from datetime import datetime

import rasterio as rio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject
from rasterio.enums import Resampling

import shapely
from shapely import wkt
from shapely import ops
from shapely.geometry import shape

from functools import partial

import pyproj

import fiona

from tabulate import tabulate

from pandas import to_datetime
from datetime import datetime, timedelta


@click.group()
def s2():
    pass


@s2.command()
@click.argument("destination")
@click.option(
    "--image_date",
    "date",
    help="Date of image collection.",
    type=click.DateTime(formats=["%Y-%m-%d"]),
)
@click.option("--search_window", help="Imagery search window.", default=2)
@click.option("--footprint", help="Data footprint geojson (within <dir>!).")
@click.option("--chooser", "choose", help="show chooser", is_flag=True)
def get_image(
    footprint, date, search_window, destination, bands=["B03", "B11"], choose=False
):
    """
    Retrieves sentinel-2 scenes.

    Scenes must entirely contain <footprint>
    within date +/- search_window.

    Downloads <bands> to
    <dir>/sentinel2.

    Requires SCIHUB_USERNAME and SCIHUB_PASSWORD environment variables.
    """
    print("Searching for Sentinel-2 Imagery...")
    workdir = path.join(destination, "sentinel-2")
    makedirs(workdir, exist_ok=True)

    api = SentinelAPI(
        environ["SCIHUB_USERNAME"],
        environ["SCIHUB_PASSWORD"],
        "https://scihub.copernicus.eu/dhus",
    )
    footprint_wkt = geojson_to_wkt(read_geojson(path.join(destination, footprint)))
    footprint_geom = wkt.loads(footprint_wkt)

    date_window = timedelta(days=search_window)
    date_range = (date - date_window, date + date_window)
    q = api.query(footprint_wkt, date=date_range, platformname="Sentinel-2")
    results = api.to_dataframe(q)

    # filter results
    does_overlap = [
        wkt.loads(i_fp).contains(footprint_geom) for i_fp in results.footprint
    ]
    results = results[does_overlap]
    print("Overlapping scenes: {}".format(len(results)))
    results.to_csv(path.join(workdir, "s2-collects.csv"))

    # choose result that's closest in time
    results["timedeltas"] = (date - results.datatakesensingstart).abs()
    results = results.sort_values(by="timedeltas", ascending=True)

    image_iloc = 0
    if choose:
        print(
            tabulate(
                results[
                    ["datatakesensingstart", "cloudcoverpercentage", "timedeltas"]
                ].reset_index(drop=True),
                headers="keys",
            )
        )
        image_iloc = int(input("Choose image ID [0-{}]: ".format(len(results) - 1)))

    # build request for AWS data.
    tile_name, time, aws_index = AwsTile.tile_id_to_tile(
        results.iloc[image_iloc].level1cpdiidentifier
    )
    metafiles = ["tileInfo", "preview"]
    request = AwsTileRequest(
        tile=tile_name,
        time=time,
        aws_index=aws_index,
        bands=bands,
        metafiles=metafiles,
        data_folder=workdir,
        data_source=DataSource.SENTINEL2_L1C,
    )

    if input("Download? (y/n): ").lower() == "y":
        request.save_data()
    else:
        print("Aborted.")
        return None

    dateparts = time.split("-")
    zero_pad_date = "{:d}-{:02d}-{:d}".format(
        int(dateparts[0]), int(dateparts[1]), int(dateparts[2])
    )

    imgpath = path.join(
        workdir, ",".join([str(tile_name), zero_pad_date, str(aws_index)])
    )
    print(imgpath)
    return imgpath


@s2.command()
@click.argument("dir")
@click.option("--reproject", "projection", help="EPSG code to reproject NDSI to.")
@click.option("--threshold", "threshold", help="NDSI Threshold for binarization")
@click.option("--clip", help="GeoJSON file to clip NDSI to.")
def compute_ndsi(dir, projection=None, threshold=None, clip=None):
    """
    Computes NDSI for s2 image contained in <dir>.

    S2_NDSI = (B03 - B11) / (B03 + B11)
    (https://earth.esa.int/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm)

    B03 = 10 m resolution
    B11 = 20 m resolution

    We resample B11 to B03 (10 m) resolution before NDSI.

    If threshold is given, NDSI is thresholded to binary.

    If projection is given, final NDSI is re-projected to given epsg.
    """
    print("Computing NDSI.")

    b03 = rio.open(path.join(dir, "B03.jp2"))
    b11 = rio.open(path.join(dir, "B11.jp2"))

    print("Resampling B11...")
    b03_data = b03.read().squeeze() / 10000.0
    b11_data = (
        b11.read(
            out_shape=(b03.count, b03.width, b03.height),  # match b03
            resampling=Resampling.cubic,
        ).squeeze()
        / 10000.0
    )

    print("Computing NDSI...")
    NDSI = ((b03_data - b11_data) / (b03_data + b11_data)).astype("float32")

    NDSI_dst_profile = b03.meta.copy()

    # new file is a float geotiff always
    NDSI_dst_profile["driver"] = "GTiff"
    NDSI_dst_profile["tiled"] = "true"
    NDSI_dst_profile["compress"] = "lzw"
    NDSI_dst_profile["dtype"] = rio.dtypes.float32

    if threshold is not None:
        NDSI = (NDSI >= float(threshold)).astype("uint16")
        # change dtype for smaller file sizes
        NDSI_dst_profile["dtype"] = rio.dtypes.uint16

    if projection:
        print("Reprojecting to {}...".format(projection))
        # compute projection from b03 CRS to new
        d_transform, d_width, d_height = calculate_default_transform(
            b03.crs, projection, b03.width, b03.height, *b03.bounds  # new crs
        )  # original
        NDSI_dst_profile.update(
            {
                "crs": projection,
                "transform": d_transform,
                "width": d_width,
                "height": d_height,
            }
        )
        print("writing NDSI.")
        with rio.open(path.join(dir, "NDSI.tif"), "w", **NDSI_dst_profile) as NDSI_dst:
            reproject(
                source=NDSI,
                destination=rio.band(NDSI_dst, 1),
                src_transform=b03.transform,
                src_crs=b03.crs,
                dst_transform=d_transform,
                dst_crs=projection,
                resampling=Resampling.bilinear,
            )
    else:
        print("writing NDSI.")
        with rio.open(path.join(dir, "NDSI.tif"), "w", **NDSI_dst_profile) as NDSI_dst:
            NDSI_dst.write(NDSI, 1)

    if clip:
        with rio.open(path.join(dir, "NDSI.tif")) as ndsi_src:
            ## NOTICE: USES FIRST FEATURE ONLY
            clip = fiona.open(clip)
            clip_geom = shape(clip[0]["geometry"])
            print(clip.crs["init"], ndsi_src.crs["init"])
            project = partial(
                pyproj.transform,
                pyproj.Proj(init=clip.crs["init"]),  # source coordinate system
                pyproj.Proj(init=ndsi_src.crs["init"]),
            )  # destination coordinate system
            clip_geom_xform = ops.transform(project, clip_geom)

            ndsi_clip, ndsi_clip_xform = mask(
                ndsi_src, [clip_geom_xform], crop=True, nodata=9999
            )

            ndsi_clipped_profile = ndsi_src.meta.copy()
            ndsi_clipped_profile.update(
                {
                    "height": ndsi_clip.shape[1],
                    "width": ndsi_clip.shape[2],
                    "transform": ndsi_clip_xform,
                    "nodata": 9999,
                }
            )
            with rio.open(
                path.join(dir, "NDSI-clipped.tif"), "w", **ndsi_clipped_profile
            ) as ndsi_clipped_dst:
                ndsi_clipped_dst.write(ndsi_clip)


@click.command()
@click.argument("figdir")
@click.option("--ndsi", help="Compute NDSI from S2 imagery.", is_flag=True)
@click.option("--chooser", help="Show S2 Asset Chooser", is_flag=True)
def get_sentinel(**kwargs):
    """
    Download overlapping sentinel2 imagery for NDSI computation.
    """
    image_date = kwargs.get("image_date")
    root_dir = kwargs.get("figdir")
    footprint = read_geojson(path.join(root_dir, kwargs.get("footprint")))

    s2path = get_sentinel_image(
        footprint,
        image_date,
        kwargs.get("search_window"),
        root_dir,
        choose=kwargs.get("chooser"),
    )

    if kwargs.get("ndsi"):
        if kwargs.get("clip"):
            clip = fiona.open(path.join(root_dir, kwargs.get("footprint")))
        else:
            clip = None
        compute_ndsi(
            s2path,
            projection=kwargs.get("reproject"),
            threshold=kwargs.get("ndsi_threshold"),
            clip=clip,
        )


if __name__ == "__main__":
    s2()
