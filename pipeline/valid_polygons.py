import rasterio as rio
from tempfile import NamedTemporaryFile
from rasterio.features import shapes

import subprocess

import numpy

import sys
import os 

os.environ['CURL_CA_BUNDLE']='/etc/ssl/certs/ca-certificates.crt'

import argparse

def main():
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument("gt_file")
    parser.add_argument("output")
    
    args = parser.parse_args()
    
    # read file (singleband raster)
    f = rio.open(args.gt_file)
    
    # make mask
    print("Masking...", end="", flush=True)
    data = f.read(1)
    mask = numpy.invert(numpy.isnan(data)) # relies on rasterio to read nan for nodata. 
    print("done.")
    # write to tmpfile

    print("Polygonize..", end="", flush=True)
    prof = f.profile.copy()
    prof.update({'compress' : 'lzw'})
    prof.update({'dtype': 'uint8'})
    prof.pop("nodata", None)
    
    temp = NamedTemporaryFile(suffix = '.tif')
    
    with rio.open(temp.name, 'w', **prof) as dst:
        dst.write(mask.squeeze().astype('uint8'), 1)
        dst.close()

    try: 
        subprocess.check_output(['gdal_polygonize.py', 
                                 temp.name, 
                                 '-f',
                                 'GeoJSON', 
                                 args.output])
    except subprocess.CalledProcessError as e:
        print ("polygonize failed:\n", e.output)

    temp.close()
    print('done.')
    
    print("Reprojecting...", end="", flush=True)
    # reproject
    try: 
        newfile = os.path.splitext(args.output)[0] + "_4326.geojson"
        subprocess.check_output(['ogr2ogr',
                                 '-where',
                                 'DN=1',
                                 "-t_srs",
                                 "EPSG:4326",
                                 newfile, 
                                 args.output])
        
    except subprocess.CalledProcessError as e:
        print ("reproject failed:\n", e.output)
    print('done.')
    
    return
    
if __name__ == "__main__" : 
    sys.exit(main())
    
    
    