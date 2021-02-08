from sklearn import metrics

METRICS = ["Precision", "Recall", "F-Score", "Balanced Accuracy", "Kappa"]

import click
import json
import numpy as np

import os
import shutil
import subprocess
import warnings

from hashlib import md5
import rasterio as rio

import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="ticks", context="talk")
plt.style.use("dark_background")

import ast


class PythonLiteralOption(click.Option):
    def type_cast_value(self, ctx, value):
        try:
            return ast.literal_eval(value)
        except:
            raise click.BadParameter(value)


def _barplot(data, labels, ax, firstcolor=True):
    inds = range(len(labels))
    colors = np.full(len(labels), plt.rcParams["axes.prop_cycle"].by_key()["color"][0])
    if firstcolor:
        colors[0] = "red"

    ax.set_xticks(inds)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1)
    ax.set_yticks(np.arange(0, 1, 0.1))
    ax.bar(inds, data, width=0.35, color=colors)


def plot_performance(performance, dir, labels=None):
    dataTypes = list(performance.keys())

    fig, ax = plt.subplots(1, len(METRICS), figsize=(4.67 * len(METRICS), 4.5))
    axes = ax.reshape(-1)
    for m_i, metric in enumerate(METRICS):
        data = [performance[dt][metric] for dt in dataTypes]
        if labels:
            _barplot(data, labels, axes[m_i])
        else:
            _barplot(data, dataTypes, axes[m_i])
        axes[m_i].set_title(metric)

    plt.tight_layout()

    plt.savefig(os.path.join(dir, "results_combined.pdf"))


def compute_performance(true, pred, nodata=-9999):

    mask = true.mask
    true = true.data[~mask]

    pred = pred.data[~mask]

    print(np.shape(true), np.shape(pred))

    if len(np.unique(true)) != len(np.unique(pred)):
        if len(np.unique(true)) > len(np.unique(pred)):
            true[true == nodata] = 0
        else:
            pred[pred == nodata] = 0

    assert pred.shape == true.shape

    print(np.unique(true), np.unique(pred))

    with warnings.catch_warnings():
        warnings.filterwarnings("error")

        try:
            performance = metrics.precision_recall_fscore_support(
                true, pred, average="binary"
            )

            accuracy = metrics.balanced_accuracy_score(true, pred)

            kappa = metrics.cohen_kappa_score(true, pred)
        except exceptions.UndefinedMetricWarning:
            print("One or more metrics Undefined. Skipping.")
            return None

    result = {
        "Precision": performance[0],
        "Recall": performance[1],
        "F-Score": performance[2],
        "Balanced Accuracy": accuracy,
        "Kappa": kappa,
    }

    return result


def _coarsen(asoPath, comparatorPath, outdir=None, data_region=None):
    """
    Creates a virtual raster with ASO and comparator stacked (aso band 1).
    
    Uses data_region.geojson in the ASO directory to clip the VRT. 
    """

    gdalCmd = (
        'gdalbuildvrt -overwrite -resolution lowest -separate -r nearest -vrtnodata "-9999 -9999" {output}.vrt {aso} {comparator} && '
        "gdalwarp -overwrite -cutline {cutline} -crop_to_cutline -dstnodata -9999 {output}.vrt {output}_clipped.vrt "
    )

    if outdir is None:
        outdir = os.path.join(os.path.dirname(asoPath), "coarsened")
        os.makedirs(outdir, exist_ok=True)

    comparatorOutfileRoot = os.path.join(
        outdir, "ASO_vs_" + os.path.splitext(os.path.basename(comparatorPath))[0]
    )
    if data_region:
        cutlinePath = data_region
    else:
        cutlinePath = os.path.join(os.path.dirname(asoPath), "data_region.geojson")

    _cmd = gdalCmd.format(
        aso=asoPath,
        comparator=comparatorPath,
        output=comparatorOutfileRoot,
        cutline=cutlinePath,
    )
    print(_cmd)
    subprocess.Popen(["/bin/bash", "-c", _cmd], shell=False).communicate()

    return comparatorOutfileRoot + "_clipped.vrt"


@click.command()
@click.argument("TRUE", nargs=1)
@click.argument("PREDS", nargs=-1)
@click.option(
    "--out_directory",
    "-od",
    "out_directory",
    required=False,
    type=str,
    default="/tmp",
    show_default=True,
)
@click.option("--gdal_conda", "-gdal", "gdal", help="Conda Env with GDAL")
@click.option("--data_region", help="OGR file to delineate comparision region.")
@click.option("--epsg", help="Common projection to project into")
@click.option(
    "--plot_labels", help="Labels for Plot", cls=PythonLiteralOption, default=[]
)
@click.option("--prefix", help="output folder prefix", default="metrics")
def compare_all(
    true, preds, out_directory, gdal, data_region, epsg, plot_labels, coarsen, prefix
):
    workfiles = (true,) + preds
    # generate experiment id
    run_id = md5()
    run_id.update("-".join(workfiles).encode("utf-8"))

    # create work directory
    workdir = os.path.join(out_directory, f"{prefix}_{run_id.hexdigest()}")
    os.makedirs(workdir, exist_ok=True)

    # reproject + copy all files to work out_directory
    shutil.copy(data_region, os.path.join(workdir, "data_region.geojson"))

    filenames = []
    for file in workfiles[1:]:
        outname = _coarsen(
            workfiles[0], file, workdir, os.path.join(workdir, "data_region.geojson")
        )
        filenames.append(outname)

    performance = {}

    for i, comparison in enumerate(filenames):
        print("Reading {}".format(comparison))
        data = rio.open(comparison)
        truth_data = data.read(1, masked=True)
        pred_data = data.read(2, masked=True)  # 1-indexed and band=1 is truth.

        performance[comparison] = compute_performance(truth_data, pred_data)

    with open(os.path.join(workdir, run_id.hexdigest() + "_results.json"), "w") as f:
        json.dump(performance, f)

    plot_performance(performance, workdir, plot_labels)

    print("Results located at: {}".format(workdir))
    print("Done.")
    return


if __name__ == "__main__":
    compare_all()
