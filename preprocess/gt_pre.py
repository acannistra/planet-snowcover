import argparse

def add_parser(subparser):
    parser = subparser.add_parser(
        "gt_pre", help = "Preprocess ground truth data.",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--gt_file", help="ground truth filename.",
                        required=True)
    parser.add_argument("--threshold", help="threshold for ")
    parser.add_argument("output_dir", help="output directory. (AWS S3 and GCP GS compatible).")

    parser.set_defaults(func = main)

def main(args):
    print("in gt_pre. args: {}".format(str(args)))
