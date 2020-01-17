from sklearn import metrics
METRICS = ["Precision", "Recall", "F-Score", "Balanced Accuracy", "Kappa"]

import click
import json
import numpy as np

import os
import shutil
import subprocess

from hashlib import md5
import rasterio as rio

import matplotlib.pyplot as plt
import seaborn as sns
sns.set(style="ticks", context="talk")
plt.style.use('dark_background')

import ast

class PythonLiteralOption(click.Option):

    def type_cast_value(self, ctx, value):
        try:
            return ast.literal_eval(value)
        except:
            raise click.BadParameter(value)


def _barplot(data, labels, ax, firstcolor=True):
    inds = range(len(labels))
    colors = np.full(len(labels),
                     plt.rcParams['axes.prop_cycle'].by_key()['color'][0])
    if firstcolor:
        colors[0] = 'red'

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
        data = [performance[dt][m_i] for dt in dataTypes]
        if labels:
            _barplot(data, labels, axes[m_i])
        else:
            _barplot(data, dataTypes, axes[m_i])
        axes[m_i].set_title(metric)

    plt.tight_layout()

    plt.savefig(os.path.join(dir, "results_combined.pdf"))


def compute_performance(true, pred, nodata = -9999):

    true = true.flatten()
    true = true[~(true == nodata)]

    pred = pred.flatten()
    pred = pred[~(pred == nodata)]

    assert(pred.shape == true.shape)

    performance = metrics.precision_recall_fscore_support(true, pred, average = 'binary')

    accuracy = metrics.balanced_accuracy_score(true, pred)

    kappa = metrics.cohen_kappa_score(true, pred)

    return(performance[:3] + (accuracy, kappa,))


@click.command()
@click.argument('TRUE', nargs=1)
@click.argument('PREDS', nargs=-1)
@click.option('--out_directory', '-od', 'out_directory', required=False, type=str,  default = "/tmp", show_default=True)
@click.option("--gdal_conda", '-gdal', "gdal", help="Conda Env with GDAL")
@click.option("--data_region", help="OGR file to delineate comparision region.")
@click.option("--epsg", help='Common projection to project into')
@click.option("--plot_labels", help="Labels for Plot", cls = PythonLiteralOption, default=[])
def compare_all(true, preds, out_directory, gdal, data_region, epsg, plot_labels):
    workfiles = (true,) + preds
    # generate experiment id
    run_id = md5()
    run_id.update("-".join(workfiles).encode("utf-8"))

    # create work directory
    workdir = os.path.join(out_directory, run_id.hexdigest())
    os.makedirs(workdir, exist_ok=True)

    # reproject + copy all files to work out_directory
    shutil.copy(data_region, workdir)

    filenames = []
    for file in workfiles:
        basename = os.path.basename(file)
        dest_file = os.path.join(workdir, basename)
        filenames.append(basename)
        command = 'bash -c "source activate {}; \
                   gdalwarp -t_srs {} {} {}"'.format(gdal,epsg,file, dest_file)
        subprocess.run(command, shell=True)

    # align files to truth for comparision:
    print(workdir)
    merged_out_root = run_id.hexdigest() + "_comparator"
    merge_files = " ".join(filenames)
    command = 'bash -c "source activate {}; \
                cd {}; \
                gdal_merge.py -separate -o {} \
                {}"'.format(gdal, workdir, merged_out_root+".tif", merge_files)
    print(command)
    a = subprocess.run(command, shell=True)


    # -co COMPRESS=LZW
    # clip to standard data region
    command = 'bash -c "source activate {}; \
                        cd {}; \
                        gdalwarp -cutline {} -crop_to_cutline \
                        -co COMPRESS=LZW -co BIGTIFF=YES -dstnodata -9999 {} {}"'.format(gdal, workdir, data_region, merged_out_root+".tif", merged_out_root+"_clipped.tif")
    print(command)
    a = subprocess.run(command,
                        shell=True)

    performance = {}

    databrick = rio.open(os.path.join(workdir, merged_out_root + "_clipped.tif"))
    truth = databrick.read(1)


    for i, pred in enumerate(filenames[1:]): # skip truth
        print("Reading {}".format(pred))
        pred_data = databrick.read(i + 2) # 1-indexed and band=1 is truth.

        performance[pred] = compute_performance(truth, pred_data)


    with open(os.path.join(workdir, run_id.hexdigest() + "_results.json"), 'w') as f:
        json.dump(performance, f)


    plot_performance(performance, workdir, plot_labels)

    print("Results located at: {}".format(workdir))
    print("Done.")
    return

if __name__ == '__main__':
    compare_all()
