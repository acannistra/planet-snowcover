""" Dictionary-based configuration with a TOML-based on-disk representation. Cf: https://github.com/toml-lang/toml """

import sys
import toml


def check_config(config):
    """Check if config file is consistent. Exit on error if not."""

    if "dataset" not in config.keys():
        sys.exit("dataset path is mandatory in config file")

    if "channels" not in config.keys():
        sys.exit("At least one channel is mandatory in config file")

    for channel in config["channels"]:
        if not (len(channel["bands"]) == len(channel["mean"]) == len(channel["std"])):
            sys.exit("Inconsistent channel bands, mean or std lenght in config file")


def load_config(path):
    """Loads a dictionary from configuration file."""

    config = toml.load(path)
    check_config(config)

    return config


def save_config(attrs, path):
    """Saves a configuration dictionary to a file."""

    toml.dump(attrs, path)
