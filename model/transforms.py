"""
transforms.py

image transforms

"""

import torchvision
import numpy as np

class __arbitrary:

    def __init__(self, f, *args):
        self.np_f = f
        self.args = args

    def __call__(self, image):
        return(self.np_f(image, *self.args))


class AsType:

    def __init__(self, type):
        self.type = type

    def __call__(self, np_array):

        return np_array.astype(self.type)

class Transpose:

    def __init__(self, transpose):
        self.transpose = transpose

    def __call__(self, np_array):

        return np.transpose(np_array, self.transpose)


class JointTransform:
    """Callable to compose non-joint transformations into joint-transformations on image and mask.

    Note: must not be used with stateful transformations (e.g. rngs) which need to be in sync for image and mask.
    """

    def __init__(self, image_transform, mask_transform):
        """Creates an `JointTransform` instance.

        Args:
          image_transform: the transformation to run on the image or `None` for no-op.
          mask_transform: the transformation to run on the mask or `None` for no-op.

        Returns:
          The (image, mask) tuple with the transformations applied.
        """

        self.image_transform = image_transform
        self.mask_transform = mask_transform

    def __call__(self, image, mask):
        """Applies the transformations associated with images and their mask.

        Args:
          images: the PIL.Image images to transform.
          mask: the PIL.Image mask to transform.

        Returns:
          The PIL.Image (images, mask) tuple with images and mask transformed.
        """

        if self.image_transform is not None:
            image = self.image_transform(image)

        if self.mask_transform is not None:
            mask = self.mask_transform(mask)

        return image, mask

class JointCompose:
    """Callable to transform an image and it's mask at the same time.
    """

    def __init__(self, transforms):
        """Creates an `JointCompose` instance.

        Args:
          transforms: list of tuple with (image, mask) transformations.
        """

        self.transforms = transforms

    def __call__(self, image, mask):
        """Applies multiple transformations to the images and the mask at the same time.

        Args:
          images: the PIL.Image images to transform.
          mask: the PIL.Image mask to transform.

        Returns:
          The transformed PIL.Image (images, mask) tuple.
        """

        for transform in self.transforms:
            image, mask = transform(image, mask)

        return image, mask
