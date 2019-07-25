#!/usr/bin/env python3

import os
import sys
import argparse

import pkgutil
from importlib import import_module

import robosat_pink.tools


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog="./rsp")
    subparser = parser.add_subparsers(title="RoboSat.pink tools", metavar="")

    try:
        module = import_module("robosat_pink.tools.{}".format(sys.argv[1]))
        module.add_parser(subparser)
    except:
        path = os.path.dirname(robosat_pink.tools.__file__)

        for tool in [name for _, name, _ in pkgutil.iter_modules([path]) if name != "__main__"]:
            if os.access("{}.py".format(os.path.join(path, tool)), os.X_OK):
                module = import_module("robosat_pink.tools.{}".format(tool))
                module.add_parser(subparser)

    subparser.required = True
    args = parser.parse_args()
    args.func(args)
