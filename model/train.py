import os
import sys
import argparse
import collections
from contextlib import contextmanager

from PIL import Image

import torch
import torch.backends.cudnn
from torch.nn import DataParallel
from torch.optim import Adam
from torch.utils.data import DataLoader
from torchvision.transforms import Normalize

from tqdm import tqdm

from numpy import *
from math import floor

from numpy.random import randint

from .transforms import *
from .datasets import *
#
# from robosat.transforms import (
#     JointCompose,
#     JointTransform,
#     ##JointResize,
#     JointRandomFlipOrRotate,
#     ImageToTensor,
#     MaskToTensor,
# )
from robosat.datasets import SlippyMapTilesConcatenation
from robosat.metrics import Metrics
from robosat.losses import CrossEntropyLoss2d, mIoULoss2d, FocalLoss2d, LovaszLoss2d
from .unet import UNet
from robosat.utils import plot
from robosat.config import load_config
from robosat.log import Log


@contextmanager
def no_grad():
    with torch.no_grad():
        yield


def add_parser(subparser):
    parser = subparser.add_parser(
        "train", help="trains model on dataset", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--config", type=str, required=True, help="path to configuration file")
    parser.add_argument("--checkpoint_url", type=str, required=False, help="path to a model checkpoint (to retrain)")
    parser.add_argument("--save_intermed", action='store_true',
    help="save intermediate checkpoints", default=False)
    parser.add_argument("out", type=str, help="directory to save checkpoint .pth files and log")

    parser.set_defaults(func=main)


def main(args):
    config = load_config(args.config)
    print(config)
    lr = args.lr if args.lr else config["model"]["lr"]
    dataset_path = args.dataset if args.dataset else config["dataset"]["path"]
    num_epochs = args.epochs if args.epochs else config["model"]["epochs"]

    log = Log(os.path.join(args.out, "log"))

    if torch.cuda.is_available():
        device = torch.device("cuda")

        torch.backends.cudnn.benchmark = True
        log.log("RoboSat - training on {} GPUs, with {} workers".format(torch.cuda.device_count(), args.workers))
    else:
        device = torch.device("cpu")
        print(args.workers)
        log.log("RoboSat - training on CPU, with {} workers". format(args.workers))

    num_classes = len(config["classes"]["titles"])
    num_channels = 0
    for channel in config["channels"]:
        num_channels += len(channel["bands"])
    pretrained = config["model"]["pretrained"]
    net = DataParallel(UNet(num_classes, num_channels=num_channels, pretrained=pretrained)).to(device)

    if config["model"]["loss"] in ("CrossEntropy", "mIoU", "Focal"):
        try:
            weight = torch.Tensor(config["classes"]["weights"])
        except KeyError:
            sys.exit("Error: The loss function used, need dataset weights values")

    optimizer = Adam(net.parameters(), lr=lr, weight_decay=config["model"]["decay"])

    resume = 0
    if args.checkpoint:

        def map_location(storage, _):
            return storage.cuda() if torch.cuda.is_available() else storage.cpu()

        # https://github.com/pytorch/pytorch/issues/7178
        chkpt = torch.load(args.checkpoint, map_location=map_location)
        net.load_state_dict(chkpt["state_dict"])
        log.log("Using checkpoint: {}".format(args.checkpoint))

        if args.resume:
            optimizer.load_state_dict(chkpt["optimizer"])
            resume = chkpt["epoch"]

    if config["model"]["loss"] == "CrossEntropy":
        criterion = CrossEntropyLoss2d(weight=weight).to(device)
    elif config["model"]["loss"] == "mIoU":
        criterion = mIoULoss2d(weight=weight).to(device)
    elif config["model"]["loss"] == "Focal":
        criterion = FocalLoss2d(weight=weight).to(device)
    elif config["model"]["loss"] == "Lovasz":
        criterion = LovaszLoss2d().to(device)
    else:
        sys.exit("Error: Unknown [model][loss] value !")

    train_loader, val_loader = get_dataset_loaders(dataset_path, config, args.workers)

    if resume >= num_epochs:
        sys.exit("Error: Epoch {} set in {} already reached by the checkpoint provided".format(num_epochs, args.config))

    history = collections.defaultdict(list)

    log.log("")
    log.log("--- Input tensor from Dataset: {} ---".format(dataset_path))
    num_channel = 1
    for channel in config["channels"]:
        for band in channel["bands"]:
            log.log("Channel {}:\t\t {}[band: {}]".format(num_channel, channel["sub"], band))
            num_channel += 1
    log.log("")
    log.log("--- Hyper Parameters ---")
    log.log("Batch Size:\t\t {}".format(config["model"]["batch_size"]))
    log.log("Image Size:\t\t {}".format(config["model"]["image_size"]))
    log.log("Data Augmentation:\t {}".format(config["model"]["data_augmentation"]))
    log.log("Learning Rate:\t\t {}".format(lr))
    log.log("Weight Decay:\t\t {}".format(config["model"]["decay"]))
    log.log("Loss function:\t\t {}".format(config["model"]["loss"]))
    log.log("ResNet pre-trained:\t {}".format(config["model"]["pretrained"]))
    if "weight" in locals():
        log.log("Weights :\t\t {}".format(config["dataset"]["weights"]))
    log.log("")

    for epoch in range(resume, num_epochs):

        log.log("---")
        log.log("Epoch: {}/{}".format(epoch + 1, num_epochs))

        train_hist = train(train_loader, num_classes, device, net, optimizer, criterion)
        log.log(
            "Train    loss: {:.4f}, mIoU: {:.3f}, {} IoU: {:.3f}, MCC: {:.3f}".format(
                train_hist["loss"],
                train_hist["miou"],
                config["classes"]["titles"][1],
                train_hist["fg_iou"],
                train_hist["mcc"],
            )
        )

        for k, v in train_hist.items():
            history["train " + k].append(v)

        val_hist = validate(val_loader, num_classes, device, net, criterion)
        log.log(
            "Validate loss: {:.4f}, mIoU: {:.3f}, {} IoU: {:.3f}, MCC: {:.3f}".format(
                val_hist["loss"], val_hist["miou"], config["classes"]["titles"][1], val_hist["fg_iou"], val_hist["mcc"]
            )
        )

        for k, v in val_hist.items():
            history["val " + k].append(v)
        visual_path = os.path.join(args.out, "history-{:05d}-of-{:05d}.png".format(epoch + 1, num_epochs))
        plot(visual_path, history)

        if (args.save_intermed):
            states = {"epoch": epoch + 1, "state_dict": net.state_dict(), "optimizer": optimizer.state_dict()}
            checkpoint_path = os.path.join(args.out, "checkpoint-{:05d}-of-{:05d}.pth".format(epoch + 1, num_epochs))
            torch.save(states, checkpoint_path)


def train(loader, num_classes, device, net, optimizer, criterion):
    num_samples = 0
    running_loss = 0

    metrics = Metrics(range(num_classes))

    net.train()

    for images, masks in tqdm(loader, desc="Train", unit="batch", ascii=True):
        images = images.to(device)
        masks = masks.to(device)

        print(images.size(), masks.size())
        print(images.size()[2:],  masks.size()[1:])
        assert images.size()[2:] == masks.size()[1:], "resolutions for images and masks are in sync"

        num_samples += int(images.size(0))

        optimizer.zero_grad()
        outputs = net(images)

        assert outputs.size()[2:] == masks.size()[1:], "resolutions for predictions and masks are in sync"
        assert outputs.size()[1] == num_classes, "classes for predictions and dataset are in sync"

        loss = criterion(outputs, masks)
        loss.backward()

        optimizer.step()

        running_loss += loss.item()

        for mask, output in zip(masks, outputs):
            prediction = output.detach()
            metrics.add(mask, prediction)

    assert num_samples > 0, "dataset contains training images and labels"

    return {
        "loss": running_loss / num_samples,
        "miou": metrics.get_miou(),
        "fg_iou": metrics.get_fg_iou(),
        "mcc": metrics.get_mcc(),
    }


@no_grad()
def validate(loader, num_classes, device, net, criterion):
    num_samples = 0
    running_loss = 0

    metrics = Metrics(range(num_classes))

    net.eval()

    for images, masks in tqdm(loader, desc="Validate", unit="batch", ascii=True):
        images = images.to(device)
        masks = masks.to(device)

        assert images.size()[2:] == masks.size()[1:], "resolutions for images and masks are in sync"

        num_samples += int(images.size(0))

        outputs = net(images)

        assert outputs.size()[2:] == masks.size()[1:], "resolutions for predictions and masks are in sync"
        assert outputs.size()[1] == num_classes, "classes for predictions and dataset are in sync"

        loss = criterion(outputs, masks)

        running_loss += loss.item()

        for mask, output in zip(masks, outputs):
            metrics.add(mask, output)

    assert num_samples > 0, "dataset contains validation images and labels"

    return {
        "loss": running_loss / num_samples,
        "miou": metrics.get_miou(),
        "fg_iou": metrics.get_fg_iou(),
        "mcc": metrics.get_mcc(),
    }


def get_dataset_loaders(dataset_path, config, workers):


    batch_size = config['model']["batch_size"]
    train_percent = config['dataset']['train_percent']
    path = dataset_path

    transform = JointCompose(
        [
            #JointRandomFlipOrRotate(config["model"]["data_augmentation"]),
            JointTransform(AsType(float), AsType(float)),
            JointTransform(ImageToTensor(), MaskToTensor()),
            #JointTransform(Normalize(mean=mean, std=std), None),
        ]
    )


    #
    # transform = JointCompose(
    #     [
    #         JointTransform(AsType(float32), AsType(float32)),
    #         #JointTransform(Transpose((1,2,0)), Transpose((1,2,0))),
    #         JointTransform(TensorFromNumpy(), TensorFromNumpy())
    #         #JointTransform(ImageToTensor(), MaskToTensor())
    #         # JointTransform(ConvertImageMode("RGB"), ConvertImageMode("P")),
    #         # JointTransform(Resize(target_size, Image.BILINEAR), Resize(target_size, Image.NEAREST)),
    #         # JointTransform(CenterCrop(target_size), CenterCrop(target_size)),
    #         # JointRandomHorizontalFlip(0.5),
    #         # JointRandomRotation(0.5, 90),
    #         # JointRandomRotation(0.5, 90),
    #         # JointRandomRotation(0.5, 90),
    #         # JointTransform(ImageToTensor(), MaskToTensor()),
    #         # JointTransform(Normalize(mean=mean, std=std), None),
    #     ]
    # )

    data_tiles = PairedTiles(
        os.path.join(path, "images"),
        os.path.join(path, "mask"), transform
    )

    num_images = len(data_tiles)

    all_indices = set(range(num_images))

    num_train = floor(num_images * train_percent)
    train_indices = randint(0, num_images, num_train)

    test_indices = all_indices - set(train_indices)

    train_tiles = PairedTiles(os.path.join(path, "images"),
                              os.path.join(path, "mask"),
                              transform, list(train_indices))

    test_tiles = PairedTiles(os.path.join(path, "images"),
                             os.path.join(path, "mask"),
                             transform, list(test_indices))


    train_loader = DataLoader(train_tiles, batch_size=batch_size, shuffle=True, drop_last=True, num_workers=workers)
    val_loader = DataLoader(test_tiles, batch_size=batch_size, shuffle=False, drop_last=True, num_workers=workers)

    return train_loader, val_loader
