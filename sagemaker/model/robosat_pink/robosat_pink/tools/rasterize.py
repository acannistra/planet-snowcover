import argparse
import collections
import json
import os
import sys

import numpy as np
from PIL import Image
from tqdm import tqdm

import mercantile
from rasterio.crs import CRS
from rasterio.transform import from_bounds
from rasterio.features import rasterize
from rasterio.warp import transform
from supermercado import burntiles

from robosat_pink.config import load_config
from robosat_pink.colors import make_palette, complementary_palette
from robosat_pink.tiles import tiles_from_csv
from robosat_pink.web_ui import web_ui
from robosat_pink.logs import Logs


def add_parser(subparser):
    parser = subparser.add_parser(
        "rasterize",
        help="rasterize GeoJSON features to raster labels",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--config", type=str, required=True, help="path to configuration file")
    parser.add_argument("--zoom", type=int, required=True, help="zoom level of tiles")
    parser.add_argument("--tile_size", type=int, help="if set, override tile size value from config file")
    parser.add_argument("--web_ui", action="store_true", help="activate web ui output")
    parser.add_argument("--web_ui_base_url", type=str, help="web ui alternate base url")
    parser.add_argument("--web_ui_template", type=str, help="path to an alternate web ui template")
    parser.add_argument("features", type=str, nargs="+", help="path to GeoJSON features file")
    parser.add_argument("cover", type=str, help="path to csv tiles cover file")
    parser.add_argument("out", type=str, help="directory to write converted images")

    parser.set_defaults(func=main)


def feature_to_mercator(feature):
    """Convert polygon feature coords to 3857.

    Args:
      feature: geojson feature to convert to mercator geometry.
    """
    # Ref: https://gist.github.com/dnomadb/5cbc116aacc352c7126e779c29ab7abe

    # FIXME: We assume that GeoJSON input coordinates can't be anything else than EPSG:4326
    if feature["geometry"]["type"] == "Polygon":
        xys = (zip(*ring) for ring in feature["geometry"]["coordinates"])
        xys = (list(zip(*transform(CRS.from_epsg(4326), CRS.from_epsg(3857), *xy))) for xy in xys)

        yield {"coordinates": list(xys), "type": "Polygon"}


def burn(tile, features, tile_size, burn_value=1):
    """Burn tile with features.

    Args:
      tile: the mercantile tile to burn.
      features: the geojson features to burn.
      tile_size: the size of burned image.
      burn_value: the value you want in the output raster where a shape exists

    Returns:
      image: rasterized file of size with features burned.
    """

    shapes = ((geometry, burn_value) for feature in features for geometry in feature_to_mercator(feature))

    bounds = mercantile.xy_bounds(tile)
    transform = from_bounds(*bounds, tile_size, tile_size)

    return rasterize(shapes, out_shape=(tile_size, tile_size), transform=transform)


def main(args):
    config = load_config(args.config)
    tile_size = args.tile_size if args.tile_size else config["model"]["tile_size"]
    colors = [classe["color"] for classe in config["classes"]]

    os.makedirs(args.out, exist_ok=True)

    # We can only rasterize all tiles at a single zoom.
    assert all(tile.z == args.zoom for tile in tiles_from_csv(args.cover))

    # Find all tiles the features cover and make a map object for quick lookup.
    feature_map = collections.defaultdict(list)
    log = Logs(os.path.join(args.out, "log"), out=sys.stderr)

    def parse_polygon(feature_map, polygon, i):

        try:
            for i, ring in enumerate(polygon["coordinates"]):  # GeoJSON coordinates could be N dimensionals
                polygon["coordinates"][i] = [[x, y] for point in ring for x, y in zip([point[0]], [point[1]])]

            for tile in burntiles.burn([{"type": "feature", "geometry": polygon}], zoom=args.zoom):
                feature_map[mercantile.Tile(*tile)].append({"type": "feature", "geometry": polygon})

        except ValueError:
            log.log("Warning: invalid feature {}, skipping".format(i))

        return feature_map

    def parse_geometry(feature_map, geometry, i):

        if geometry["type"] == "Polygon":
            feature_map = parse_polygon(feature_map, geometry, i)

        elif geometry["type"] == "MultiPolygon":
            for polygon in geometry["coordinates"]:
                feature_map = parse_polygon(feature_map, {"type": "Polygon", "coordinates": polygon}, i)
        else:
            log.log("Notice: {} is a non surfacic geometry type, skipping feature {}".format(geometry["type"], i))

        return feature_map

    for feature in args.features:
        with open(feature) as f:
            fc = json.load(f)
            for i, feature in enumerate(tqdm(fc["features"], ascii=True, unit="feature")):

                if feature["geometry"]["type"] == "GeometryCollection":
                    for geometry in feature["geometry"]["geometries"]:
                        feature_map = parse_geometry(feature_map, geometry, i)
                else:
                    feature_map = parse_geometry(feature_map, feature["geometry"], i)

    # Burn features to tiles and write to a slippy map directory.
    for tile in tqdm(list(tiles_from_csv(args.cover)), ascii=True, unit="tile"):
        if tile in feature_map:
            out = burn(tile, feature_map[tile], tile_size)
        else:
            out = np.zeros(shape=(tile_size, tile_size), dtype=np.uint8)

        out_dir = os.path.join(args.out, str(tile.z), str(tile.x))
        os.makedirs(out_dir, exist_ok=True)

        out_path = os.path.join(out_dir, "{}.png".format(tile.y))

        if os.path.exists(out_path):
            prev = np.array(Image.open(out_path))
            out = np.maximum(out, prev)

        out = Image.fromarray(out, mode="P")

        out_path = os.path.join(args.out, str(tile.z), str(tile.x))
        os.makedirs(out_path, exist_ok=True)

        out.putpalette(complementary_palette(make_palette(colors[0], colors[1])))
        out.save(os.path.join(out_path, "{}.png".format(tile.y)), optimize=True)

    if args.web_ui:
        template = "leaflet.html" if not args.web_ui_template else args.web_ui_template
        base_url = args.web_ui_base_url if args.web_ui_base_url else "./"
        tiles = [tile for tile in tiles_from_csv(args.cover)]
        web_ui(args.out, base_url, tiles, tiles, "png", template)
