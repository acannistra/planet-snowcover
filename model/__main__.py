"""
model

implementation of a neural network based image segmentation pipeline for the identification of snow in satellite imagery.

"""

import argparse

from model import *

def add_parsers():
    parser = argparse.ArgumentParser(prog="model")
    subparser = parser.add_subparsers(title="tools", metavar = "")

    ## individual tool parsers
    ...

    subparser.required = True

    return parser.parse_args()

if __name__ == "__main__":
    args = add_parsers()
    args.func(args)
