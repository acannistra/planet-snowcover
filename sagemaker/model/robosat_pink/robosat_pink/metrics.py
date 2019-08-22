import torch
import math
import numpy as np

from sklearn import metrics

class Metrics:
    """Tracking mean metrics """

    def __init__(self):
        self.tn = 0
        self.fn = 0
        self.fp = 0
        self.tp = 0

    def add(self, label, predicted, is_prob=True):
        """Adds an observation to the tracker.

        Args:
          label: the ground truth labels.
          predicted: the predicted prob or mask.
          is_prob: as predicted could be either a prob or a mask.
        """

        if is_prob:
            # predicted = torch.argmax(predicted, 0)
            predicted = predicted > 0 ## SINGLE CLASS ONLY~!!

        confusion = predicted.view(-1).float() / label.view(-1).float()

        self.tn += torch.sum(torch.isnan(confusion)).item()
        self.fn += torch.sum(confusion == float("inf")).item()
        self.fp += torch.sum(confusion == 0).item()
        self.tp += torch.sum(confusion == 1).item()

    def get_miou(self):
        """Retrieves the mean Intersection over Union score."""

        try:
            miou = np.nanmean([self.tn / (self.tn + self.fn + self.fp), self.tp / (self.tp + self.fn + self.fp)])
        except ZeroDivisionError:
            miou = float("NaN")

        return miou

    def get_fg_iou(self):
        """Retrieves the foreground Intersection over Union score."""

        try:
            iou = self.tp / (self.tp + self.fn + self.fp)
        except ZeroDivisionError:
            iou = float("NaN")

        return iou

    def get_mcc(self):
        """Retrieves the Matthew's Coefficient Correlation score."""

        try:
            mcc = (self.tp * self.tn - self.fp * self.fn) / math.sqrt(
                (self.tp + self.fp) * (self.tp + self.fn) * (self.tn + self.fp) * (self.tn + self.fn)
            )
        except ZeroDivisionError:
            mcc = float("NaN")

        return mcc

    def get_classification_stats(self):

        try:
            accuracy = (self.tp + self.tn) / (self.tp + self.fp + self.fn + self.tn)
            precision = self.tp / (self.tp + self.fp)
            recall = self.tp / (self.tp + self.tn)
            f1 = 2 * (recall * precision) / (recall + precision)
        except ZeroDivisionError:
            return {
                "accuracy": -1,
                "precision": -1, 
                "recall": -1, 
                "f1": -1
            }

        return {
            "accuracy" : accuracy,
            "precision" : precision,
            "recall" : recall,
            "f1" : f1
        }
