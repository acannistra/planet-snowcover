"""PyTorch-compatible datasets.

Guaranteed to implement `__len__`, and `__getitem__`.

See: https://pytorch.org/docs/stable/data.html
"""

import os
import sys
import torch
from PIL import Image
import torch.utils.data
import cv2
import numpy as np
import rasterio as rio
from mercantile import Tile


from robosat_pink.tiles import tiles_from_slippy_map, buffer_tile_image, tiles_from_slippy_map_s3
"""
datasets.py

utilities for loading imagery datasets

"""

import torch.utils.data

from mercantile import Tile

from copy import deepcopy

import rasterio as rio
from rasterio.session import AWSSession

from itertools import chain

import os

import numpy as np

import s3fs
import boto3

import pandas as pd



class PairedTiles(torch.utils.data.Dataset):
    """ Pairs images with mask from <image> and <tiles> directories
    based on tile information encoded in filenames, e.g.:
        images/12_123_66_0.tif --> masks/12_123_66_0.tif
    etc
    """

    def __init__(self, imagedir, maskdir, joint_transform = None, indices = None):
        """
        imagedir: flat directory of N-band TIFF images as above

        maskdir: flat directory of 1-band TIFF masks as above

        joint_transform = a transforms.JointTransform object to apply to data

        indices = optional list of 0-indexed image indices for subsetting.

        """
        super().__init__()

        self.joint_transform = joint_transform

        self.imagedir = imagedir
        self.maskdir = maskdir

        self.images = os.listdir(imagedir)
        self.masks = os.listdir(maskdir)

        print(self.imagedir)

        if indices is not None:
            self.images = [self.images[i] for i in indices]

        self.imagetiles = [Tile(*f.split("_")[:3]) for f in self.images]
        self.masktiles = [Tile(*f.split("_")[:3]) for f in self.masks]


        assert (set(self.imagetiles).issubset(set(self.masktiles))), "Image and Mask tilesets must be equal!"


    def __len__(self):
        return len(self.images)



    def __getitem__(self, i):
        ## 1. grab, open image i
        ## 2. grab, open corresponding mask
        imageFile = self.images[i]
        maskFile = "{}_{}_{}_0.tif".format(*imageFile.split('_')[:3])

        image = rio.open(os.path.join(self.imagedir, imageFile)).read()
        mask = rio.open(os.path.join(self.maskdir, maskFile)).read()
        mask = np.squeeze(mask)

        if self.joint_transform:
            augmented = self.joint_transform(image=image, mask=mask)
            image = augmented['image']
            mask = augmented['mask']

        return(image, torch.from_numpy(mask).long())


# Single Slippy Map directory structure
class S3SlippyMapTiles(torch.utils.data.Dataset):
    """Dataset for images stored in slippy map format on AWS S3
    """

    def __init__(self, root, mode, transform=None, aws_profile = 'default'):
        super().__init__()

        self.tiles = []
        self.transform = transform
        self.aws_profile = aws_profile

        self.tiles = [(id, tile, path) for id, tile, path in tiles_from_slippy_map_s3(root, aws_profile)]
        self.tiles.sort(key=lambda tile: tile[0])
        self.mode = mode

    def __len__(self):
        return len(self.tiles)

    def __getitem__(self, i):
        id, tile, path = self.tiles[i]


        image = None
        with rio.Env(profile_name=self.aws_profile):

            if self.mode == "image":
                image = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)

            elif self.mode == "multibands":
                image = rio.open(path).read()

            elif self.mode == "mask":
                image = np.array(Image.open(path).convert("P"))

            if self.transform is not None:
                image = self.transform(image = image)['image']


        return tile, torch.FloatTensor(image)




# Single Slippy Map directory structure
class SlippyMapTiles(torch.utils.data.Dataset):
    """Dataset for images stored in slippy map format.
    """

    def __init__(self, root, mode, transform=None, tile_index = False):
        super().__init__()

        self.tiles = []
        self.transform = transform
        self.tile_index = tile_index

        self.tiles = [(tile, path) for tile, path in tiles_from_slippy_map(root)]
        if tile_index:
            self.tiles = dict(self.tiles)

        #self.tiles.sort(key=lambda tile: tile[0])
        self.mode = mode

    def __len__(self):
        return len(self.tiles)

    def __getitem__(self, i):

        tile, path = self.tiles[i]

        if self.mode == "image":
            image = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)

        elif self.mode == "multibands":
            image = rio.open(path).read()

        elif self.mode == "mask":
            image = np.array(Image.open(path).convert("P"))

        if self.transform is not None:
            image = self.transform(image = image)['image']


        return tile, image


class MultiSlippyMapTilesConcatenation(torch.utils.data.Dataset):
    """
        supports multiple image and mask slippy mask directories.

        ensures that each image tile is matched with a mask tile.

        unique source directory identifiers are used to support tile overlap (e.g. if SourceDir1 has tile 200/15/6 and SourceDir2 has tile 200/15/6, both are preserved, one of the MaskSourceDirs contains 200/15/6 )
    """

    def __init__(self, imageSources, maskSources, joint_transform = None, aws_profile = None, image_ids = None):
        super().__init__()

        self.aws_profile = aws_profile
        self.joint_transform = joint_transform
        self.image_ids = image_ids

        # see if we need to remove s3://
        self.trim_protocol = False
        if all([i.startswith('s3://') and m.startswith('s3://') for i, m in zip(imageSources, maskSources)]):
            self.trim_protocol = True

        datacols = ['id', 'tile', 'path']

        self.imagery = list(chain.from_iterable([tiles_from_slippy_map_s3(src, aws_profile = aws_profile, trim_protocol = self.trim_protocol) for src in imageSources]))

        self.masks = list(chain.from_iterable([tiles_from_slippy_map_s3(src, aws_profile = aws_profile, trim_protocol = self.trim_protocol) for src in maskSources]))


        self.imagery = pd.DataFrame(self.imagery, columns = datacols)
        self.masks = pd.DataFrame(self.masks, columns = datacols)

        ## match masks with imagery
        self.overlap = self.imagery.set_index('tile').join(self.masks.set_index('tile'),
         how = 'inner', rsuffix = '_mask')
        self.overlap  = self.overlap.set_index('id')

        if (self.image_ids is not None):
            self.overlap = self.overlap.loc[self.image_ids]

        self.image_ids = self.overlap.index.values


    def __len__(self):
        return(len(self.overlap))

    def getIds(self):
        return self.image_ids

    def __getitem__(self, i):

        match = self.overlap.iloc[i]

        s = boto3.Session(profile_name = self.aws_profile)

        with rio.Env(AWSSession(s)):
            mask = np.squeeze(rio.open(match.path_mask).read())
            data = rio.open(match.path).read()


        if self.joint_transform:
            augmented = self.joint_transform(image=data, mask=mask)
            data = augmented['image']
            mask = augmented['mask']

        return(torch.FloatTensor(data), torch.from_numpy(mask).double(), match.name)





# Paired Image and Mask slippy map directories.
class SlippyMapTilesConcatenation(torch.utils.data.Dataset):
    """Dataset to concate multiple input images stored in slippy map format.
    """

    def __init__(self, path, target, tiles = None, joint_transform=None, aws_profile = None):
        super().__init__()

        self._data_on_s3 = False
        if (path.startswith("s3://") and target.startswith("s3://")):
            self._data_on_s3 = True

            self.inputs = tiles_from_slippy_map_s3(path,
                                                   aws_profile = aws_profile)

            self.target = tiles_from_slippy_map_s3(target,
                                                   aws_profile = aws_profile)

        else:

            self.inputs = SlippyMapTiles(path, mode='multibands')

            self.target = SlippyMapTiles(target, mode="multibands")




        self.inputs = dict(self.inputs)
        self.target = dict(self.target)

        data_tiles = self.inputs.keys()
        mask_tiles = self.target.keys()

        self.tiles = list(set(data_tiles).intersection(set(mask_tiles)))

        if (tiles is not None):
            # only use those tiles specified in `tiles` argument
            self.tiles = [t for t in self.tiles if t in tiles]
            print(len(self.tiles))



        self.inputs = {tile : path for tile, path in self.inputs.items() if tile in self.tiles}
        self.target = {tile : path for tile, path in self.target.items() if tile in self.tiles}

        # No transformations in the `SlippyMapTiles` instead joint transformations in getitem
        self.joint_transform = joint_transform

    def __len__(self):
        return len(self.tiles)

    def __getitem__(self, i):

        tile = self.tiles[i]

        if(self._data_on_s3):
            # open and read files at __getitem__
            mask = rio.open(self.target[tile]).read()
            data = rio.open(self.inputs[tile]).read()
        else:
            # open and read files already happened.
            mask = self.target[tile]
            data = self.inputs[tile]



        # for channel in self.channels:
        #     try:
        #         data, band_tile = self.inputs[channel["sub"]][i]
        #         assert band_tile == tile
        #
        #         for band in channel["bands"]:
        #             data_band = data[:, :, int(band) - 1] if len(data.shape) == 3 else []
        #             data_band = data_band.reshape(mask.shape[0], mask.shape[1], 1)
        #             tensor = np.concatenate((tensor, data_band), axis=2) if "tensor" in locals() else data_band  # noqa F821
        #     except:
        #         sys.exit("Unable to concatenate input Tensor")

        if self.joint_transform is not None:
            transformed = self.joint_transform(image = data, mask = mask)
            data = transformed['image']
            mask = transformed['mask']


        return torch.FloatTensor(data), mask.squeeze(), tile


# Todo: once we have the SlippyMapDataset this dataset should wrap
# it adding buffer and unbuffer glue on top of the raw tile dataset.
class BufferedSlippyMapDirectory(torch.utils.data.Dataset):
    """Dataset for buffered slippy map tiles with overlap.
    """

    def __init__(self, root, transform=None, size=512, overlap=32):
        """
        Args:
          root: the slippy map directory root with a `z/x/y.png` sub-structure.
          transform: the transformation to run on the buffered tile.
          size: the Slippy Map tile size in pixels
          overlap: the tile border to add on every side; in pixel.

        Note:
          The overlap must not span multiple tiles.

          Use `unbuffer` to get back the original tile.
        """

        super().__init__()

        assert overlap >= 0
        assert size >= 256

        self.transform = transform
        self.size = size
        self.overlap = overlap
        self.tiles = list(tiles_from_slippy_map(root))

    def __len__(self):
        return len(self.tiles)

    def __getitem__(self, i):
        tile, path = self.tiles[i]
        image = np.array(buffer_tile_image(tile, self.tiles, overlap=self.overlap, tile_size=self.size))

        if self.transform is not None:
            image = self.transform(image)

        return image, torch.IntTensor([tile.x, tile.y, tile.z])

    def unbuffer(self, probs):
        """Removes borders from segmentation probabilities added to the original tile image.

        Args:
          probs: the segmentation probability mask to remove buffered borders.

        Returns:
          The probability mask with the original tile's dimensions without added overlap borders.
        """

        o = self.overlap
        _, x, y = probs.shape

        return probs[:, o : x - o, o : y - o]
