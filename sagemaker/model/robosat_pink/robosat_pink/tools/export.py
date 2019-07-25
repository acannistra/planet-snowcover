import os
import sys
import argparse

import pkgutil
from importlib import import_module

import torch
import torch.onnx
import torch.autograd

from robosat_pink.config import load_config
import robosat_pink.models


def add_parser(subparser):
    parser = subparser.add_parser(
        "export", help="exports or prunes a trained model", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--config", type=str, required=True, help="path to configuration file")
    parser.add_argument("--export_channels", type=int, help="export channels to use (keep the first ones)")
    parser.add_argument("--type", type=str, choices=["onnx", "pth"], default="onnx", help="output type")
    parser.add_argument("--tile_size", type=int, help="if set, override tile size value from config file")
    parser.add_argument("--checkpoint", type=str, required=True, help="model checkpoint to load")
    parser.add_argument("out", type=str, help="path to save export model to")

    parser.set_defaults(func=main)


def main(args):
    config = load_config(args.config)
    tile_size = args.tile_size if args.tile_size else config["model"]["tile_size"]

    if args.type == "onnx":
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        # Workaround: PyTorch ONNX, DataParallel with GPU issue, cf https://github.com/pytorch/pytorch/issues/5315

    num_classes = len(config["classes"])
    num_channels = 0
    for channel in config["channels"]:
        num_channels += len(channel["bands"])

    export_channels = num_channels if not args.export_channels else args.export_channels
    assert num_channels >= export_channels, "Will be hard indeed, to export more channels than thoses dataset provide"

    def map_location(storage, _):
        return storage.cpu()

    encoder = config["model"]["encoder"]
    pretrained = config["model"]["pretrained"]

    models = [name for _, name, _ in pkgutil.iter_modules([os.path.dirname(robosat_pink.models.__file__)])]
    if config["model"]["name"] not in [model for model in models]:
        sys.exit("Unknown model, thoses available are {}".format([model for model in models]))

    model_module = import_module("robosat_pink.models.{}".format(config["model"]["name"]))
    net = getattr(model_module, "{}".format(config["model"]["name"].title()))(
        num_classes=num_classes, num_channels=num_channels, encoder=encoder, pretrained=pretrained
    ).to("cpu")

    chkpt = torch.load(args.checkpoint, map_location=map_location)
    net = torch.nn.DataParallel(net)
    net.load_state_dict(chkpt["state_dict"])

    if export_channels < num_channels:
        weights = torch.zeros((64, export_channels, 7, 7))
        weights.data = net.module.resnet.conv1.weight.data[:, :export_channels, :, :]
        net.module.resnet.conv1 = torch.nn.Conv2d(num_channels, 64, kernel_size=7, stride=2, padding=3, bias=False)
        net.module.resnet.conv1.weight = torch.nn.Parameter(weights)

    if args.type == "onnx":
        batch = torch.autograd.Variable(torch.randn(1, export_channels, tile_size, tile_size))
        torch.onnx.export(net, batch, args.out)

    elif args.type == "pth":
        states = {"epoch": chkpt["epoch"], "state_dict": net.state_dict(), "optimizer": chkpt["optimizer"]}
        torch.save(states, args.out)
