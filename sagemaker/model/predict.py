import os
from os import environ
import sys
import io
from os.path import expanduser
sys.path.append("../model/robosat_pink/")

from importlib import import_module
import pkgutil

import boto3
import s3fs
import argparse

from re import match

import sklearn

from numpy.random import randint
import numpy as np

import robosat_pink.losses
import robosat_pink.models
from robosat_pink.datasets import S3SlippyMapTiles
from robosat_pink.tools.train import get_dataset_loaders
from robosat_pink.config import load_config
from robosat_pink.logs import Logs
from robosat_pink.metrics import Metrics

import torch
import torch.backends.cudnn
from torch.optim import Adam
from torch.utils.data import DataLoader

import matplotlib.pyplot as plt

def main():
    ap = argparse.ArgumentParser(description='run model on tileset')
    ap.add_argument('model', help='path to model checkpoint')
    ap.add_argument('config', help='path to model config')
    ap.add_argument('tiles', help='path to XYZ tile folder')
    ap.add_argument('--aws_profile', help='AWS Profile Name', default = 'default')

    args = ap.parse_args()

    config = load_config(args.config)
    tiles = S3SlippyMapTiles(args.tiles, mode = 'multimode', aws_profile = args.aws_profile)
    net = model(config)


    loader = DataLoader(train_tileset,
                        batch_size = config['model']['batch_size'],
                        shuffle = True,
                        num_workers = 1)

    predict(net, loader)




def predict(net, loader):
    net.eval()

    for _tile, image in tqdm(loader, desc="Predict", unit="batch", ascii=True):
        print(_tile)
        # with torch.no_grad():
        #     raw = model(images)

def model(config):

    if torch.cuda.is_available():
        device = torch.device("cuda")
        torch.backends.cudnn.benchmark = True
    else:
        device = torch.device("cpu")


    num_classes = len(config["classes"])
    num_channels = 0
    for channel in config["channels"]:
        num_channels += len(channel["bands"])
    pretrained = config["model"]["pretrained"]
    encoder = config["model"]["encoder"]

    models = [name for _, name, _ in pkgutil.iter_modules([os.path.dirname(robosat_pink.models.__file__)])]
    if config["model"]["name"] not in [model for model in models]:
        sys.exit("Unknown model, thoses available are {}".format([model for model in models]))

    model_module = import_module("robosat_pink.models.{}".format(config["model"]["name"]))
    net = getattr(model_module, "{}".format(config["model"]["name"].title()))(
        num_classes=num_classes, num_channels=num_channels, encoder=encoder, pretrained=pretrained
    ).to(device)

    net = torch.nn.DataParallel(net)


    def map_location(storage, _):
        return storage.cuda() if torch.cuda.is_available() else storage.cpu()
    try:
        if S3_CHECKPOINT:
            with s3fs.S3File(fs, trainedModel, 'rb') as C:
                state = torch.load(io.BytesIO(C.read()), map_location = map_location)
        else:
            state = torch.load(trainedModel, map_location= map_location)
        net.load_state_dict(state['state_dict'])
        net.to(device)
    except FileNotFoundError as f:
        print("{} checkpoint not found.".format(CHECKPOINT))

    losses = [name for _, name, _ in pkgutil.iter_modules([os.path.dirname(robosat_pink.losses.__file__)])]
    if config["model"]["loss"] not in [loss for loss in losses]:
        sys.exit("Unknown loss, thoses available are {}".format([loss for loss in losses]))

    loss_module = import_module("robosat_pink.losses.{}".format(config["model"]["loss"]))
    criterion = getattr(loss_module, "{}".format(config["model"]["loss"].title()))().to(device)

    return net, device

if __name__ == "__main__":
    main()
