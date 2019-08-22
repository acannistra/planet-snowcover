import os
import sys
import argparse
import pprint
os.environ['CURL_CA_BUNDLE']='/etc/ssl/certs/ca-certificates.crt'

import torch
import torch.backends.cudnn
from torch.optim import Adam
from torch.utils.data import DataLoader
from torchvision.transforms import Normalize

import s3fs
import boto3
import io
from re import match

from tqdm import tqdm

import pkgutil
from importlib import import_module

from robosat_pink.transforms import (
    JointCompose,
    JointTransform,
    JointResize,
    JointRandomFlipOrRotate,
    ImageToTensor,
    MaskToTensor,
    AsType
)

from robosat_pink.datasets import MultiSlippyMapTilesConcatenation
from robosat_pink.metrics import Metrics
from robosat_pink.config import load_config
from robosat_pink.logs import Logs
import robosat_pink.losses
import robosat_pink.models

from sklearn.model_selection import train_test_split


from numpy import floor, array
from numpy.random import randint

import albumentations as A


def add_parser(subparser):
    parser = subparser.add_parser(
        "train", help="trains a model on a dataset", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--config", type=str, required=True, help="path to configuration file")
    parser.add_argument("--checkpoint", type=str, required=False, help="path to a model checkpoint (to retrain)")
    parser.add_argument("--workers", type=int, required=False, default=1)

    parser.add_argument("out", type=str)

    parser.set_defaults(func=main)


def main(args):
    config = load_config(args.config)
    print(config)

    log = Logs(os.path.join(args.out, "log"))

    if torch.cuda.is_available():
        device = torch.device("cuda")

        torch.backends.cudnn.benchmark = True
        log.log("RoboSat - training on {} GPUs, with {} workers".format(torch.cuda.device_count(), args.workers))
    else:
        device = torch.device("cpu")
        log.log("RoboSat - training on CPU, with {} workers".format(args.workers))

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
    optimizer = Adam(net.parameters(), lr=config["model"]["lr"], weight_decay=config["model"]["decay"])

    resume = 0

    # check checkpoint situation  + load if ncessary
    checkpoint = None # no checkpoint
    if args.checkpoint: # command line checkpoint
        checkpoint = args.checkpoint
    try: # config file checkpoint
        checkpoint = config["checkpoint"]['path']
    except:
        # no checkpoint in config file
        pass


    S3_CHECKPOINT = False
    if checkpoint:

        if checkpoint.startswith("s3://"):
            S3_CHECKPOINT = True
            # load from s3
            checkpoint = checkpoint[5:]
            sess = boto3.Session(profile_name=config['dataset']['aws_profile'])
            fs = s3fs.S3FileSystem(session=sess)
            s3ckpt = s3fs.S3File(fs, checkpoint, 'rb')

        def map_location(storage, _):
            return storage.cuda() if torch.cuda.is_available() else storage.cpu()

    if checkpoint is not None:
        def map_location(storage, _):
            return storage.cuda() if torch.cuda.is_available() else storage.cpu()
        try:
            if S3_CHECKPOINT:
                with s3fs.S3File(fs, checkpoint, 'rb') as C:
                    state = torch.load(io.BytesIO(C.read()),
                                       map_location = map_location)
            else:
                state = torch.load(checkpoint)
            optimizer.load_state_dict(state['optimizer'])
            net.load_state_dict(state['state_dict'])
            net.to(device)
        except FileNotFoundError as f:
            print("{} checkpoint not found.".format(CHECKPOINT))

        log.log("Using checkpoint: {}".format(checkpoint))


    losses = [name for _, name, _ in pkgutil.iter_modules([os.path.dirname(robosat_pink.losses.__file__)])]
    if config["model"]["loss"] not in [loss for loss in losses]:
        sys.exit("Unknown loss, thoses available are {}".format([loss for loss in losses]))

    loss_module = import_module("robosat_pink.losses.{}".format(config["model"]["loss"]))
    criterion = getattr(loss_module, "{}".format(config["model"]["loss"].title()))().to(device)

    train_loader, val_loader = get_dataset_loaders(config, args.workers, idDir = args.out)

    if resume >= config["model"]["epochs"]:
        sys.exit(
            "Error: Epoch {} set in {} already reached by the checkpoint provided".format(
                config["model"]["epochs"], args.config
            )
        )

    log.log("")
    log.log("--- Input tensor from Dataset: {} ---".format(config["dataset"]["image_bucket"] + '/' +
             config['dataset']['imagery_directory_regex']))

    log.log("")
    log.log("--- Hyper Parameters ---")
    log.log("Model:\t\t\t {}".format(config["model"]["name"]))
    log.log("Encoder model:\t\t {}".format(config["model"]["encoder"]))
    log.log("Loss function:\t\t {}".format(config["model"]["loss"]))
    log.log("ResNet pre-trained:\t {}".format(config["model"]["pretrained"]))
    log.log("Batch Size:\t\t {}".format(config["model"]["batch_size"]))
    log.log("Tile Size:\t\t {}".format(config["model"]["tile_size"]))
    log.log("Data Augmentation:\t {}".format(config["model"]["data_augmentation"]))
    log.log("Learning Rate:\t\t {}".format(config["model"]["lr"]))
    log.log("Weight Decay:\t\t {}".format(config["model"]["decay"]))
    log.log("")

    for epoch in range(resume, config["model"]["epochs"]):

        log.log("---")
        log.log("Epoch: {}/{}".format(epoch + 1, config["model"]["epochs"]))

        train_hist = train(train_loader, num_classes, device, net, optimizer, criterion)
        log.log(
            "Train    loss: {:.4f}, mIoU: {:.3f}, IoU: {:.3f}, precision:  {:.3f}, recall: {:.3f}".format(
                train_hist["loss"],
                train_hist["miou"],
                train_hist["fg_iou"],
                train_hist["precision"],
                train_hist["recall"],
            )
        )

        val_hist = validate(val_loader, num_classes, device, net, criterion)
        log.log(
            "Validate loss: {:.4f}, mIoU: {:.3f}, IoU: {:.3f}, precision:  {:.3f}, recall: {:.3f}".format(
                train_hist["loss"],
                train_hist["miou"],
                train_hist["fg_iou"],
                train_hist["precision"],
                train_hist["recall"],
            )
        )

        states = {"epoch": epoch + 1, "state_dict": net.state_dict(), "optimizer": optimizer.state_dict()}
        checkpoint_path = os.path.join(
            args.out, "checkpoint-{:05d}-of-{:05d}.pth".format(epoch + 1, config["model"]["epochs"])
        )
        torch.save(states, checkpoint_path)


def train(loader, num_classes, device, net, optimizer, criterion):
    num_samples = 0
    running_loss= 0

    metrics = Metrics()

    net.train()

    for images, masks, _tile in tqdm(loader, desc="Train", unit="batch", ascii=True):

        images = images.to(device)
        masks = masks.to(device)

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

    class_stats = metrics.get_classification_stats()

    return {
        "loss": running_loss / num_samples,
        "miou": metrics.get_miou(),
        "fg_iou": metrics.get_fg_iou(),
        "mcc": metrics.get_mcc(),
        "accuracy": class_stats['accuracy'],
        "precision" : class_stats['precision'],
        "recall" : class_stats['recall'],
        "f1": class_stats['f1']
    }


def validate(loader, num_classes, device, net, criterion):

    num_samples = 0
    running_loss = 0

    metrics = Metrics()
    net.eval()

    with torch.no_grad():
        for images, masks, _tile in tqdm(loader, desc="Validate", unit="batch", ascii=True):
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

    class_stats = metrics.get_classification_stats()


    return {
        "loss": running_loss / num_samples,
        "miou": metrics.get_miou(),
        "fg_iou": metrics.get_fg_iou(),
        "mcc": metrics.get_mcc(),
        "accuracy": class_stats['accuracy'],
        "precision" : class_stats['precision'],
        "recall" : class_stats['recall'],
        "f1": class_stats['f1']
    }


def get_dataset_loaders(config, workers, idDir=None):
    # idDir is the place to save train/test IDS as txt files.

    p = pprint.PrettyPrinter()

    fs = s3fs.S3FileSystem(session = boto3.Session(profile_name = config['dataset']['aws_profile']))

    imagery_searchpath = config['dataset']['image_bucket']  + '/' +  config['dataset']['imagery_directory_regex']
    print("Searching for imagery...({})".format(imagery_searchpath))
    imagery_candidates = fs.ls(config['dataset']['image_bucket'])
    print("candidates:")
    p.pprint(imagery_candidates)
    imagery_locs = [c for c in imagery_candidates if match(imagery_searchpath, c)]
    print("result:")
    p.pprint(imagery_locs)

    mask_searchpath = config['dataset']['mask_bucket'] + '/' +  config['dataset']['mask_directory_regex']
    print("Searching for mask...({})".format(mask_searchpath))
    mask_candidates = fs.ls(config['dataset']['mask_bucket'])
    print("candidates:")
    p.pprint(mask_candidates)
    mask_locs = [c for c in mask_candidates if match(mask_searchpath, c)]
    print("result:")
    p.pprint(mask_locs)

    assert(len(mask_locs) > 0 and len(imagery_locs) > 0)

    print("Merging tilesets...")

    allTiles = MultiSlippyMapTilesConcatenation(imagery_locs, mask_locs, aws_profile = config['dataset']['aws_profile'])
    print(len(allTiles))

    train_ids, test_ids  = train_test_split(allTiles.image_ids, train_size = config['dataset']['train_percent'])

    transform = A.Compose([
        #A.ToFloat(p = 1),
        # A.RandomRotate90(p = 0.5),
        #A.RandomRotate90(p = 0.5),
        #A.RandomRotate90(p = 0.5), #these do something bad to the bands
    #    A.Normalize(mean = mean, std = std, max_pixel_value = 1),
        A.HorizontalFlip(p = 0.5),
        A.VerticalFlip(p = 0.5),
    #    A.ToFloat(p = 1, max_value = np.finfo(np.float64).max)
    ])


    train_tileset = MultiSlippyMapTilesConcatenation(imagery_locs, mask_locs, aws_profile = config['dataset']['aws_profile'], image_ids = train_ids, joint_transform = transform)

    test_tileset =MultiSlippyMapTilesConcatenation(imagery_locs, mask_locs, aws_profile = config['dataset']['aws_profile'], image_ids = test_ids, joint_transform = transform)

    train_ids = train_tileset.getIds()
    test_ids = test_tileset.getIds()

    if idDir:
        with open(os.path.join(idDir, 'train_ids.txt'), 'w') as f:
            for item in train_ids:
                f.write("%s\n" % item)
        with open(os.path.join(idDir, 'test_ids.txt'), 'w') as f:
            for item in train_ids:
                f.write("%s\n" % item)


    train_loader = DataLoader(train_tileset,
                              batch_size = config['model']['batch_size'],
                              shuffle = True,
                              drop_last = True,
                              num_workers = workers)


    test_loader = DataLoader(test_tileset,
                             batch_size = config['model']['batch_size'],
                             shuffle = True,
                             drop_last = True,
                             num_workers = workers)

    return (train_loader, test_loader)
