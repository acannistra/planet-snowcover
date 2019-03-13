import argparse

import pandas as pd
import geopandas as gpd

import rasterio as rio
from mercantile import Tile, xy_bounds, bounds
from supermercado import burntiles

from raster_utils import reproject_raster

from rio_tiler.utils import tile_read

from os import path, makedirs

from functools import partial

import numpy as np

from concurrent import futures

import s3fs
import boto3

def add_parser(subparser):
    parser = subparser.add_parser(
        "tile", help = "Tile images.",
        description="Produce GeoTIFF tiles containing all imagery information from source image or directory of source images. OSM/XYZ Format.",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )


    parser.add_argument("output_dir", help="output directory. (AWS S3 and GCP GS compatible).")

    parser.add_argument("--cover",
                        help=".csv file containing x,y,z rows describing tiles to produce. (Default: completely cover an image)",
                        type=argparse.FileType('r'))

    parser.add_argument("--zoom", help="OSM zoom level for tiles", type=int)

    parser.add_argument("--indexes", help='band indices to include in tile.', nargs="+", type=int, default = [1,2,3,4])

    parser.add_argument("--quant", help="value to divide bands with, if quantized", type = int, default = None)
    
    parser.add_argument("--aws_profile", help='aws profile name for s3:// destinations', default = None)

    parser.add_argument("files", help="file or files to tile", nargs="+")



    parser.set_defaults(func = main)

def _write_tile(tile, image, output_dir, tile_size = 512, bands = [1,2,3,4], quant = None, aws_profile = None):
    print(quant)
    """
        extracts and writes tile from image into output_dir
    """
    tile_xy_bounds = xy_bounds(tile)
    tile_latlon_bounds = bounds(tile)
    data, mask = tile_read(image, tile_xy_bounds, tile_size, indexes=bands)
    bands, height, width = data.shape



    if quant is not None:
        data = data / quant


    dirpath = path.join(output_dir, str(tile.z), str(tile.x)).replace('\0', "")

    if(not dirpath.startswith("s3://")):
        makedirs(dirpath, exist_ok=True)

    tile_path = path.join(output_dir, str(tile.z), str(tile.x), "{}.{}".format(tile.y, "tif"))

    new_transform = rio.transform.from_bounds(*tile_latlon_bounds, width, height)

    profile = {
        'driver' : 'GTiff',
        'dtype' : data.dtype,
        'height' : height,
        'width' : width,
        'count' : bands,
        'crs' : {'init' : 'epsg:4326'},
        'transform' : new_transform
    }


#    try:
        
    ## S3 DESTINATION - use memoryfile 
    using_memoryfile = False
    if (tile_path.startswith('s3://')):
        tile_file = rio.MemoryFile()
        using_memoryfile = True
    else:
        tile_file = tile_path

    # write data to file, either on disk or memoryfile
    with rio.open(tile_file, 'w', **profile) as dst:
        for band in range(0, bands ):
            dst.write(data[band], band+1)

    # need to seek mf for reading
    if (using_memoryfile):
        tile_file.seek(0)

    ## S3 DESTINATION – write memoryfile with s3fs
    if (tile_path.startswith('s3://')):
        # strip "s3://"
        tile_path = tile_path[5:]
        # open s3 Session
        session = boto3.Session(profile_name = aws_profile)
        fs = s3fs.S3FileSystem(session=  session)
        # open file , write file
        s3fp = fs.open(tile_path, 'wb')
        s3fp.write(tile_file.read())
        # close fps
        s3fp.close()
        tile_file.close()
            
#     except Exception as e:
#         print(e)
#         return tile, False

    return tile, True


def tile_image(imageFile, output_dir, zoom, cover=None, indexes = None, quant = None, aws_profile = None):
    """
    Produce either A) all tiles covering <image> at <zoom> or B) all tiles in <cover> if <cover> is not None at <zoom> and place OSM directory structure in <imageFile>/Z/X/Y.png format inside output_dir. If quant, divide all bands by Quant first.

    """
    from shapely.geometry import box
    from json import loads
    from supermercado import burntiles

    def __load_cover_tiles(coverfile):
        coverTiles = pd.read_csv(coverfile)
        if len(coverTiles.columns) != 3:
            raise Exception("cover file needs to have 3 columns (z, x, y)")

        return [Tile(z, x, y) for _, (z, x, y) in list(coverTiles.iterrows())]

    f = rio.open(imageFile)

    # check crs:
    if int(f.crs.to_dict()['init'].split(":")[1]) != 4326:
        print(f"invalid crs ({f.crs.to_dict()['init']}), reprojecting raster....")
        f.close()
        mf = rio.io.MemoryFile()
        reproject_raster(imageFile, 4326, mf)
        mf.seek(0)

        f = mf.open()

        print(f"reproject successful {f.crs.to_dict()}")

    bbox = box(f.bounds.left, f.bounds.bottom, f.bounds.right, f.bounds.top)
    bbox = loads(gpd.GeoSeries(bbox).to_json())['features'] # need geojson dict

    tiles = [Tile(z, x, y) for z, x, y in burntiles.burn(bbox, zoom)]


    covertiles = set()
    if cover is not None:
        covertiles = set(__load_cover_tiles(cover))
        tiles = set(tiles).intersection(covertiles)


    __TILER = partial(_write_tile, image = imageFile,
                     output_dir = output_dir, bands = indexes,
                     quant = quant, aws_profile = aws_profile)

    with futures.ThreadPoolExecutor() as executor:
        responses = list(executor.map(__TILER, tiles))

    return(responses)




def main(args):
    all_tiles = []

    for image in args.files:
        fbase = path.splitext(path.basename(image))[0]
        image_output = path.join(args.output_dir, fbase)
        all_tiles.append(tile_image(image, image_output, args.zoom, args.cover, args.indexes, args.quant, args.aws_profile))
