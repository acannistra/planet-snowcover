"""
datasets.py

utilities for loading imagery datasets

"""

import torch.utils.data

from mercantile import Tile

import rasterio as rio

import os

class PairedTiles(torch.utils.data.Dataset):
    """ Pairs images with mask from <image> and <tiles> directories
    based on tile information encoded in filenames, e.g.:
        images/12_123_66_0.tif --> masks/12_123_66_0.tif
    etc
    """

    def __init__(self, imagedir, maskdir, joint_transform = None):
        super().__init__()

        self.joint_transform = joint_transform

        self.imagedir = imagedir
        self.maskdir = maskdir

        self.images = os.listdir(imagedir)
        self.masks = os.listdir(maskdir)

        self.imagetiles = [Tile(*f.split("_")[:3]) for f in self.images]
        self.masktiles = [Tile(*f.split("_")[:3]) for f in self.masks]

        assert (set(self.imagetiles) == set(self.masktiles)), "Image and Mask tilesets must be equal!"

    def __len__(self):
        return len(self.images)


    def __getitem__(self, i):
        ## 1. grab, open image i
        ## 2. grab, open corresponding mask
        ## 3. return self.joint_transform(image, mask)

        imageFile = self.images[i]
        maskFile = "{}_{}_{}_0.tif".format(*imageFile.split('_')[:3])

        image = rio.open(os.path.join(self.imagedir, imageFile)).read()
        mask = rio.open(os.path.join(self.maskdir, maskFile)).read()

        if self.joint_transform is not None:
            image, mask = self.joint_transform(image, mask)

        return(image, mask)
