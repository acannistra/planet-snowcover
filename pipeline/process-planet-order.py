import boto3
import s3fs
import pprint

from argparse import ArgumentParser

def argparser():
    parser = ArgumentParser()

    parser.add_argument('delivery_bucket', help="folder containing order id directories")
    parser.add_argument("--aws_profile")

    parser.add_argument("--order_id", required=False, help='order id to focus')

    return(parser)

def main():
    parser = argparser()
    args = parser.parse_args()

    fs = s3fs.S3FileSystem(session = boto3.Session(profile_name = args.aws_profile))
    _p = pprint.PrettyPrinter()

    orderIds = fs.ls(args.delivery_bucket)
    print("Orders:")
    _p.pprint(orderIds)



if __name__ == "__main__":
    main()
