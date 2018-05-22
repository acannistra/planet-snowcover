
# coding: utf-8

# # API Search Candidate Selection + Download
# The goal of this script is to develop the pathway from a set of single-measurement points to a set of cropped PlanetScope imagery for a given date band. 
 

#TODO: clean up this mess of imports

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, mapping, shape
from imp import reload
from numpy import mean
from image_utils import search, download
from numpy.random import randint, choice
import random
import folium
import json
import requests
from datetime import timedelta
import os
import cartopy.crs as ccrs
from cartopy import feature
from retrying import retry
from IPython.display import Image
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.patches import Circle
import numpy as np
from tqdm import tqdm
from multiprocessing.dummy import Pool as ThreadPool 

# cli
import click

#set some parameters (TODO: argparse)

@click.command()
@click.argument("imagery_dir")
@click.argument("location_file")
@click.option("--num_dates", default=10, help="number of randomly-chosen dates (default: 10)")
@click.option("--num_locs", default=20, help="number of randomly-chosen locations (default: 20)" )
@click.option("--inverse", is_flag=True, help="choose dates outside of range for controls")
@click.option("--nosearch", is_flag=True, help="only extract locations (for verification)")
@click.option("--buffer_days", default=60, help="number of days to buffer range (default: 60)")
@click.option("--id_col", help="ID column", type=click.STRING, default="id")
@click.option("--lat_col", help="latitude column", type=click.STRING, default="latitude")
@click.option("--lon_col", help="longitude column", type=click.STRING, default="longitude")
@click.option("--start_col", help="Start Date column", type=click.STRING, default="start_date")
@click.option("--end_col", help="End Date column", type=click.STRING, default="end_date")
def main(imagery_dir, location_file, num_dates, num_locs, inverse, nosearch, buffer_days,
         id_col, lat_col, lon_col, start_col, end_col):
    """
    Search Planet API for imagery of (location, date) tuples in LOCATION_FILE encompassing ground-truth
    locations and download into IMAGERY_DIR. 
    
    Assumes ["ID", latitude", "longitude", "start_date", and "end_date"] columns in LOCATION_FILE. Use options
    to change. 
    """
    NUM_RANDOM_DATES = num_dates
    NUM_RANDOM_LOCATIONS = num_locs
    INVERT_DATES = inverse
    JUST_LOCS = nosearch
    PS_BUFFER_DAYS = buffer_days
    IMAGEDIR = imagery_dir


    # ## Extract Measurement Locations

    snowdata = pd.read_csv(location_file, 
                           parse_dates = [start_col, end_col])
    snowdata['geometry'] = [Point(xy) for xy in zip(snowdata[[lon_col]].values, snowdata[[lat_col]].values)]
    snowdata = gpd.GeoDataFrame(snowdata)
    snowdata.crs = {'init' : 'epsg:4326'}

    locations = snowdata.dropna(subset=[id_col, lon_col, lat_col]).drop_duplicates(id_col)
    locations[[lon_col, lat_col]].to_csv("these_locations.csv", index_label = id_col)

    if(JUST_LOCS): exit()

    ## Select NUM_RANDOM_LOCATIONS locations

    locations = locations.loc[choice(locations.index, NUM_RANDOM_LOCATIONS, replace=False)]


    # ## Add bounding boxes

    boxes = locations[[id_col, 'geometry']].copy()
    #TODO: better understand buffer size
    boxes.geometry = [g.buffer(0.005, cap_style=3) for g in boxes.geometry]

    ## Select Dates
    if(not INVERT_DATES):
        dates = locations[[id_col, start_col, end_col]]
    else:
        timebuffer = timedelta(days=PS_BUFFER_DAYS)
        start_dates = locations[start_col]
        end_dates = locations[end_col].apply(lambda x: x + timebuffer)
        start_dates.name = "invert_buffer_start"
        end_dates.name = "invert_buffer_start"
        dates = pd.concat([locations[loc_col], start_dates, end_dates], axis=1)


    # ## Search API For Image Candidates

    if(not INVERT_DATES):
        searcher = search.Search(boxes, dates, dry=False,
                                 key=id_col, start_col='snow_appearance_date',
                                 end_col="snow_disappearance_date")
    else:
        searcher = search.Search(boxes, dates, dry=False,
                                 key='Location', start_col='snowfree_buffer_start',
                                 end_col="snowfree_buffer_end")
    results = searcher.query()


    # ## Parse Results
    # Choose `NUM_RANDOM_DATES` dates from results for each loc

    loc_img_ids = {}
    for group in results.groupby('loc_id'):
        if (len(group[1]) >= NUM_RANDOM_DATES):
            loc_img_ids[group[0]] = list(set(choice(group[1].id.values, NUM_RANDOM_DATES, replace=False)))
        else:
            loc_img_ids[group[0]] = list(set(group[1].id.values))


    files = {}
    for loc_id, img_ids in tqdm(loc_img_ids.items(), 
                               desc="Cropping + Downloading Images", 
                               unit="location", total=len(loc_img_ids)):
        box = boxes.loc[loc_id].geometry
        dl = download.CroppedDownload(loc_id, box, img_ids, IMAGEDIR)
        files[loc_id] = dl.run()


if __name__ == "__main__":
    main()