import os
import io
import sys
import argparse
sys.path.append("../model/robosat_pink/")
os.environ['CURL_CA_BUNDLE']='/etc/ssl/certs/ca-certificates.crt'

import pkgutil
from importlib import import_module

import numpy as np

import torch
import torch.backends.cudnn
from torch.utils.data import DataLoader
from torchvision.transforms import Compose, Normalize

from tqdm import tqdm
from PIL import Image

import robosat_pink.models
from robosat_pink.datasets import SlippyMapTiles, BufferedSlippyMapDirectory, S3SlippyMapTiles
from robosat_pink.tiles import tiles_from_slippy_map
from robosat_pink.config import load_config
from robosat_pink.colors import make_palette
from robosat_pink.transforms import ImageToTensor
from robosat_pink.web_ui import web_ui

import albumentations as A

import boto3
import s3fs

def add_parser(subparser):
    parser = subparser.add_parser(
        "predict",
        help="from a trained model and predict inputs, predicts masks",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--checkpoint", type=str, required=True, help="model checkpoint to load")
    parser.add_argument("--workers", type=int, default=0, help="number of workers pre-processing images")
    # parser.add_argument("--overlap", type=int, default=64, help="tile pixel overlap to predict on")
    parser.add_argument("--config", type=str, required=True, help="path to configuration file")
    parser.add_argument("--batch_size", type=int, help="if set, override batch_size value from config file")

    parser.add_argument("--aws_profile", help='aws profile for use in s3 access')

    parser.add_argument("--threshold", help='probability threshold for binarization of predictions (default = 0.0)', default = 0.0)
    parser.add_argument("--tile_size", type=int, help="if set, override tile size value from config file")
    # parser.add_argument("--web_ui", action="store_true", help="activate web ui output")
    # parser.add_argument("--web_ui_base_url", type=str, help="web ui alternate base url")
    # parser.add_argument("--web_ui_template", type=str, help="path to an alternate web ui template")
    parser.add_argument("tiles", type=str, help="directory to read slippy map image tiles from")
    parser.add_argument("probs", type=str, help="directory to save slippy map probability masks to")

    parser.set_defaults(func=main)


def main(args):
    config = load_config(args.config)
    num_classes = len(config["classes"])
    batch_size = args.batch_size if args.batch_size else config["model"]["batch_size"]
    tile_size = args.tile_size if args.tile_size else config["model"]["tile_size"]

    if torch.cuda.is_available():
        device = torch.device("cuda")
        torch.backends.cudnn.benchmark = True
    else:
        device = torch.device("cpu")

    def map_location(storage, _):
        return storage.cuda() if torch.cuda.is_available() else storage.cpu()

    # https://github.com/pytorch/pytorch/issues/7178
    # chkpt = torch.load(args.checkpoint, map_location=map_location)
    S3_CHECKPOINT = False
    chkpt = args.checkpoint
    if chkpt.startswith("s3://"):
        S3_CHECKPOINT = True
        # load from s3
        chkpt = chkpt[5:]

    models = [name for _, name, _ in pkgutil.iter_modules([os.path.dirname(robosat_pink.models.__file__)])]
    if config["model"]["name"] not in [model for model in models]:
        sys.exit("Unknown model, thoses available are {}".format([model for model in models]))

    num_channels = 0
    for channel in config["channels"]:
        num_channels += len(channel["bands"])

    pretrained = config["model"]["pretrained"]
    encoder = config["model"]["encoder"]

    model_module = import_module("robosat_pink.models.{}".format(config["model"]["name"]))

    net = getattr(model_module, "{}".format(config["model"]["name"].title()))(
        num_classes=num_classes, num_channels=num_channels, encoder=encoder, pretrained=pretrained
    ).to(device)

    net = torch.nn.DataParallel(net)


    try:
        if S3_CHECKPOINT:
            sess = boto3.Session(profile_name=args.aws_profile)
            fs = s3fs.S3FileSystem(session=sess)
            with s3fs.S3File(fs, chkpt, 'rb') as C:
                state = torch.load(io.BytesIO(C.read()), map_location = map_location)
        else:
            state = torch.load(chkpt, map_location= map_location)
        net.load_state_dict(state['state_dict'])
        net.to(device)
    except FileNotFoundError as f:
        print("{} checkpoint not found.".format(CHECKPOINT))


    net.eval()
    #
    # mean = np.array([[[8237.95084794]],
    #
    #                [[6467.98702156]],
    #
    #                [[6446.61743148]],
    #
    #                [[4520.95360105]]])
    # std  = array([[[12067.03414753]],
    #
    #                [[ 8810.00542703]],
    #
    #                [[10710.64289882]],
    #
    #                [[ 9024.92028515]]])
    # #transform = Compose([ImageToTensor(), Normalize(mean=mean, std=std)])
    # transform = A.Compose([
    #     A.Normalize(mean = mean, std = std, max_pixel_value = 1.0),
    #     A.ToFloat()
    # ])

    if args.tiles.startswith('s3://'):
        directory = S3SlippyMapTiles(args.tiles, mode='multibands', transform=None, aws_profile = args.aws_profile)
    else:
        directory = SlippyMapTiles(args.tiles, mode="multibands", transform = transform)
    # directory = BufferedSlippyMapDirectory(args.tiles, transform=transform, size=tile_size, overlap=args.overlap)
    loader = DataLoader(directory, batch_size=batch_size, num_workers=args.workers)

    palette = make_palette(config["classes"][0]["color"])


    # don't track tensors with autograd during prediction
    with torch.no_grad():
        for tiles, images in tqdm(loader, desc="Eval", unit="batch", ascii=True):
            tiles = list(zip(tiles[0], tiles[1], tiles[2]))
            images = images.to(device)
            outputs = net(images)


            print(len(tiles), len(outputs))
            for tile, prob in zip([tiles], outputs):
                savedir = args.probs
                x = tile[0].item()
                y = tile[1].item()
                z = tile[2].item()

                # manually compute segmentation mask class probabilities per pixel

                image = (prob > args.threshold).astype(np.uint8)

                out = Image.fromarray(image, mode="P")
                out.putpalette(palette)

                os.makedirs(os.path.join(args.probs, str(z), str(x)), exist_ok=True)
                path = os.path.join(args.probs, str(z), str(x), str(y) + ".png")

                out.save(path, optimize=True)

    if args.web_ui:
        template = "leaflet.html" if not args.web_ui_template else args.web_ui_template
        base_url = args.web_ui_base_url if args.web_ui_base_url else "./"
        tiles = [tile for tile, _ in tiles_from_slippy_map(args.tiles)]
        web_ui(args.probs, base_url, tiles, tiles, "png", template)
