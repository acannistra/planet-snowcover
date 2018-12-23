import argparse

def add_parser(subparser):
    parser = subparser.add_parser(
        "get_images", help = "Fetch images for given footprint and date.",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--footprint", help="desired imagery footprint.",
                        required = True)
    parser.add_argument("--date", help="date range centerpoint (YYYY/MM/DD)",
                        required = True)
    parser.add_argument("--date_range",
                        help="number of days on either side of  centerpoint to search for imagery",
                        default = 10)
    parser.add_argument("output_dir",
                        help="imagery output directory. (AWS S3 and GCP GS compatible).")

    parser.set_defaults(func = main)

def main(args):
    print("in get_images. args: {}".format(str(args)))
