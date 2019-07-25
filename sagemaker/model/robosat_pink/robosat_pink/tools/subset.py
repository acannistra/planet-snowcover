import os
import sys
import argparse
import shutil

from glob import glob
from tqdm import tqdm

from robosat_pink.tiles import tiles_from_csv
from robosat_pink.web_ui import web_ui


def add_parser(subparser):
    parser = subparser.add_parser(
        "subset",
        help="filter images in a slippy map dir using a csv tiles cover",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--mode", type=str, default="copy", choices={"copy", "move", "delete"}, help="filtering mode")
    parser.add_argument("--web_ui", action="store_true", help="activate web ui output")
    parser.add_argument("--web_ui_base_url", type=str, help="web ui alternate base url")
    parser.add_argument("--web_ui_template", type=str, help="path to an alternate web ui template")
    parser.add_argument("--dir", type=str, required=True, help="directory to read slippy map tiles from for filtering")
    parser.add_argument("--cover", type=str, required=True, help="csv cover to filter tiles by")
    parser.add_argument("--out", type=str, help="directory to save filtered tiles to (on copy or move mode)")

    parser.set_defaults(func=main)


def main(args):
    tiles = set(tiles_from_csv(args.cover))
    extension = ""

    for tile in tqdm(tiles, desc="Subset", unit="tiles", ascii=True):

        paths = glob(os.path.join(args.dir, str(tile.z), str(tile.x), "{}.*".format(tile.y)))
        if len(paths) != 1:
            print("Warning: {} skipped.".format(tile))
            continue
        src = paths[0]

        try:
            if args.mode in ["copy", "move"]:
                assert args.out
                if not os.path.isdir(os.path.join(args.out, str(tile.z), str(tile.x))):
                    os.makedirs(os.path.join(args.out, str(tile.z), str(tile.x)), exist_ok=True)

                extension = os.path.splitext(src)[1][1:]
                dst = os.path.join(args.out, str(tile.z), str(tile.x), "{}.{}".format(tile.y, extension))

            if args.mode == "move":
                assert os.path.isfile(src)
                shutil.move(src, dst)

            if args.mode == "copy":
                shutil.copyfile(src, dst)

            if args.mode == "delete":
                assert os.path.isfile(src)
                os.remove(src)

        except:
            sys.exit("Error: Unable to process {}".format(tile))

    if args.web_ui:
        template = "leaflet.html" if not args.web_ui_template else args.web_ui_template
        base_url = args.web_ui_base_url if args.web_ui_base_url else "./"
        web_ui(args.out, base_url, tiles, tiles, extension, template)
