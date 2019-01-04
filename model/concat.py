"""
concat.py

Concatenates images in slippy-map directories into a single folder. Can optionally only put images in folder which overlap with a mask (also a slippy map directory)

"""

import argparse

from os import path, makedirs

from shutil import copy2

import sys
sys.path.insert(0, 'model/robosat/')
from robosat import tiles

FILENAME_TEMPLATE = "{z}_{x}_{y}_{id}.tif"

def add_parser(subparser):
    parser = subparser.add_parser(
        "concat", help = "Concatenate XYZ image directories.",
        description = "Concatenates images in slippy-map directories into a single folder. Can optionally only put images in folder which overlap with a mask (also a slippy map directory). Output file format is {x}_{y}_{z}_{id}.tif to account for duplicate tiles across overlapping images.",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--mask_dir", help="path to directory containing tiled binary mask rasters. Only tiles present in mask will be copied from image directories.")

    parser.add_argument("output_dir", help="output directory to place image-tiles into. Will be created if it doesn't exist.")

    parser.add_argument("directories", help="Image directories to concatenate", nargs = '+')

    parser.set_defaults(func = main)



def main(args):

    imageTiles = []
    imageTileIds = set()
    discardedTiles = 0

    for dir in args.directories:
        print(path.exists(dir))
        _theseTiles = list(tiles.tiles_from_slippy_map(dir))
        _theseTileIds, _ = zip(*_theseTiles)
        if len(_theseTiles) == 0:
            print(f"Error reading tiles from: {dir}")
        else:
            imageTiles.extend(_theseTiles)
            imageTileIds = imageTileIds.union(set(_theseTileIds))


    maskTiles = []
    maskTileIds = set()

    if args.mask_dir is not None:
        num_original_tiles = len(imageTiles)
        maskTiles = list(tiles.tiles_from_slippy_map(args.mask_dir))
        maskTileIds, _ = zip(*maskTiles)

        imageTileIds = imageTileIds.intersection(set(maskTileIds))
        discardedTiles = num_original_tiles - len(imageTileIds)
        print(f"Discarded tiles: {discardedTiles}")

    makedirs(args.output_dir, exist_ok = True)

    ids = { t : 0 for t in imageTileIds }

    for tile, tile_file in imageTiles:
        if tile not in list(ids.keys()):
            print("skipping tile {}".format(tile))
            continue # ignore tile that's been discarded

        new_filename = FILENAME_TEMPLATE.format(z = tile.z,
                                                x = tile.x,
                                                y = tile.y,
                                                id = ids[tile])
        ids[tile] = ids[tile] + 1

        print("{} => {}".format(tile_file, path.join(args.output_dir, new_filename)))
        copy2(tile_file, path.join(args.output_dir, new_filename))
