import argparse

import unittest

import rasterio as rio
from rasterio.transform import guard_transform

from os import path, remove

from yaspin import yaspin
SUCCESS = "✅ "
FAIL = "💥 "

DESCRIPTION = """

Consumes ground truth data and outputs `{gt_raw}_gt_binary_raster` and `{gt_raw}_gt_footprint` into a directory. Binary raster is created either by:

* rasterizing a polygon
* thresholding a real-valued raster via `--threshold` arg, or
* doing nothing (returning input binary raster)

`{gt_raw}_gt_binary_raster.tif` and `{gt_raw}_gt_footprint.geojson` are placed into `/gt_processed` either in a cloud storage bucket or local folder.
"""

class TestGtPre(unittest.TestCase):
    def test_filetype(self):
        self.assertEqual(_filetype("test.shp"), 'shp')
        self.assertEqual(_filetype("test.tif"), 'tif')

    def test_threshold(self):
        from numpy import array_equal

        raw_aso = "https://aso.jpl.nasa.gov/_include/new_geotiff/USCATE20170129_SUPERswe_50p0m_agg.tif"
        aso_threshed = "./test/aso_thresh_01.tif"
        tmp_threshed = "./test/temp_aso_thresh.tif"

        aso_threshed = rio.open(aso_threshed)
        _threshold_raster(raw_aso,
                         tmp_threshed,
                         threshold=0.1)

        self.assertTrue(array_equal(aso_threshed.read(1),
                                    rio.open(tmp_threshed).read(1)))

        remove(tmp_threshed)

    def test_write_vector(self):
        binaryVector = "./test/aso_thresh_01.tif"
        json_representation = "./test/aso_thresh.geojson"
        json_test = "./test/test_json.geojson"

        _write_vector(binaryVector, json_test)

        correct = open(json_representation, 'r').read()
        test = open(json_test, 'r').read()

        self.assertEqual(correct, test)

    def test_check_binary(self):
        raw_aso = "https://aso.jpl.nasa.gov/_include/new_geotiff/USCATE20170129_SUPERswe_50p0m_agg.tif"
        aso_threshed = "./test/aso_thresh_01.tif"

        nonbinary = rio.open(raw_aso)
        binary = rio.open(aso_threshed)

        self.assertTrue(_is_binary_raster(binary))
        self.assertFalse(_is_binary_raster(nonbinary))



def add_parser(subparser):
    parser = subparser.add_parser(
        "gt_pre", help = "Preprocess ground truth data.",
        description = DESCRIPTION,
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--gt_file", help="ground truth filename.",
                        required=True)
    parser.add_argument("--threshold", help="threshold for ", type=float)
    parser.add_argument("output_dir", help="output directory. (AWS S3 and GCP GS compatible).")

    parser.set_defaults(func = main)

# ---

def _filetype(filename):
    "return extension of file without '.' "
    return(path.splitext(filename)[1])[1:]

def _threshold_raster(file, out_name, threshold=0.9):
    """
    writes thresholded ground-truth as single-band uint16 tiff
    """
    file = rio.open(file)
    profile = file.profile

    data = file.read(1)
    profile.update(dtype='uint16')
    profile.update(nodata = 0)
    profile.update(transform=guard_transform(profile['transform']))
    with rio.open(out_name, 'w', **profile) as dest:
        threshed = (data >= threshold)
        data = (threshed).astype('uint16')
        dest.write(data, 1)

def _write_vector(binaryRaster, outfilename):
    """
    writes vector in GeoJSON format (CRS: Lat/Lon WGS84) of polygonized input binary raster (polygon where raster == 1).
    """
    from rasterio.features import shapes
    from shapely.geometry import shape, mapping
    from shapely.ops import cascaded_union
    from geopandas import GeoDataFrame
    from json import dumps

    file = rio.open(binaryRaster)
    s = shapes(file.read(), transform = file.transform)

    s = [shape(s_i).buffer(0) for s_i, value in s if value == 1]

    largest = [sorted(s, key = lambda x: x.area, reverse=True)[0]]

    gdf = GeoDataFrame(geometry=largest, crs=file.crs)

    gdf = gdf.to_crs({'init': 'epsg:4326'}) # reproject
    with open(outfilename, 'w') as test:
        test.write(dumps(mapping(gdf.geometry.values[0])))

def _is_binary_raster(raster):
    from numpy import unique

    file = rio.open(raster)
    return(set(unique(file.read())) == set([1, 0]))

def main(args):

    file_base = path.splitext(path.basename(args.gt_file))[0]

    if not _is_binary_raster(args.gt_file):
        # not binary raster, so need a threshold
        if (args.threshold is None):
            raise Exception(f"{args.gt_file} is not a binary raster. Threshold required.")

        with yaspin(text="thresholding raster", color="yellow") as spinner:
            binrast_file = path.join(args.output_dir, f"{file_base}_binary.tif")
            _threshold_raster(args.gt_file, binrast_file, args.threshold)
            spinner.ok(SUCCESS)

    else:
        # input file is binary raster
        binrast_file = args.gt_file

    vec_filename = ".".join([file_base, 'geojson'])
    with yaspin(text="writing vector", color="yellow") as spinner:
        _write_vector(binrast_file, path.join(args.output_dir, vec_filename))
        spinner.ok(SUCCESS)
