import argparse

def add_parser(subparser):
    parser = subparser.add_parser(
        "tile", help = "Tile images.",
        description="Produce GeoTIFF tiles containing all imagery information from source image or directory of source images. OSM/XYZ Format.",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--src_dir", help="directory containing tiled images")
    group.add_argument("--image", help="single image to tile")

    parser.add_argument("output_dir", help="output directory. (AWS S3 and GCP GS compatible).")

    parser.set_defaults(func = main)

def main(args):
    print("in tile. args: {}".format(str(args)))
