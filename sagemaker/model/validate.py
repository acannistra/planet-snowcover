import os
import sys
sys.path.append("./model/robosat_pink")

import boto3
import s3fs

from robosat_pink.datasets import MultiSlippyMapTilesConcatenation
from robosat_pink.config import load_config

def main(args):
    configLoc = args[1]
    config = load_config(configLoc)

    print(config)


if __name__ == "__main__":
    main(sys.argv)
