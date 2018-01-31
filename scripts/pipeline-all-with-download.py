
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

#set some parameters (TODO: argparse)

NUM_RANDOM_DATES = 10
NUM_RANDOM_LOCATIONS = 20
YEAR = 2017
IMAGEDIR = "../images/"


# ## Extract 2017 Measurement Locations

snowdata = pd.read_csv("../data/snow_summary_all_2009_2017_locs.csv", 
                       parse_dates = ["snow_appearance_date", "snow_disappearance_date", 
                                      "date_min", "date_max"])
snowdata = snowdata[snowdata.year >= YEAR]
snowdata['geometry'] = [Point(xy) for xy in zip(snowdata.longitude, snowdata.latitude)]
snowdata = gpd.GeoDataFrame(snowdata)
snowdata.crs = {'init' : 'epsg:4326'}

locations = snowdata.dropna(subset=["longitude", 'latitude']).drop_duplicates("Location")

## Select NUM_RANDOM_LOCATIONS locations

locations = locations.loc[choice(locations.index, NUM_RANDOM_LOCATIONS, replace=False)]

# ## Add bounding boxes

boxes = locations[['Location', 'geometry']].copy()
#TODO: better understand buffer size
boxes.geometry = [g.buffer(0.005, cap_style=3) for g in boxes.geometry]


# ## Search API For Image Candidates

dates = locations[['Location', "snow_appearance_date", "snow_disappearance_date"]]
searcher = search.Search(boxes, dates, dry=False,
                         key='Location', start_col='snow_appearance_date',
                         end_col="snow_disappearance_date")
results = searcher.query()


# ## Parse Results
# Choose `NUM_RANDOM_DATES` dates from results for each loc

loc_img_ids = {}
for group in results.groupby('loc_id'):
    if (len(group[1]) >= NUM_RANDOM_DATES):
        loc_img_ids[group[0]] = list(set(choice(group[1].id.values, NUM_RANDOM_DATES, replace=False)))
    else:
        loc_img_ids[group[0]] = list(set(group[1].id.values))


reload(download)
files = {}
for loc_id, img_ids in tqdm(loc_img_ids.items(), 
                           desc="Cropping + Downloading Images", 
                           unit="location", total=len(loc_img_ids)):
    box = boxes.loc[loc_id].geometry
    dl = download.CroppedDownload(loc_id, box, img_ids, IMAGEDIR)
    files[loc_id] = dl.run()

