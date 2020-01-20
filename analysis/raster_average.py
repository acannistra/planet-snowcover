import click
import numpy as np
import rasterio as rio
import seaborn as sns
import matplotlib.pyplot as plt

@click.command()
@click.argument("file")
@click.option("--dark", "-d", is_flag=True)
def average_file(file, dark):
    f = rio.open(file)
    data = f.read(masked=True) * 100
    mean, std = np.ma.mean(data), np.ma.std(data)
    print(mean, std)

    if dark:
        plt.style.use("dark_background")
        plt.rcParams['text.color'] = 'white'
        plt.rcParams['axes.labelcolor'] = 'white'
        plt.rcParams['xtick.color'] = 'white'
        plt.rcParams['ytick.color'] = 'white'

    nonmasked_vals = data[~data.mask]
    plt.rcParams.update({'font.size': 22})



    log = False
    if len(nonmasked_vals) > 10000:
       log = True
    plt.hist(nonmasked_vals, bins = 100, log=log)
    plt.axvline(x = mean, color = 'red', linestyle = '--')
    plt.xlim(-100, 100)
    sns.despine()
    plt.ylabel("# pixels")
    plt.xlabel("Difference [% points]")
    plt.tight_layout()


    print(len(nonmasked_vals))
    plt.savefig(file+"_dist.png", dpi=300, transparent=True, layout="bbox_inches")


if __name__ == "__main__":
    average_file()
