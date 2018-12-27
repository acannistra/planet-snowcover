"""
preprocess

implementation of a pipeline to associate satellite imagery with a raster or vector ground-truth data source.

Designed to deploy to cloud storage.
"""


import argparse

from preprocess import (
    gt_pre,
    get_images,
    tile
)

def add_parsers():
    parser = argparse.ArgumentParser(prog="preprocess")
    subparser = parser.add_subparsers(title="preprocess tools", metavar="")

    gt_pre.add_parser(subparser)
    get_images.add_parser(subparser)
    tile.add_parser(subparser)

    subparser.required = True

    return parser.parse_args()

if __name__ == "__main__":
    args = add_parsers()
    args.func(args)
