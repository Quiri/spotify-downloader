from logzero import logger as log
import appdirs

import logging
import yaml
import argparse
import mimetypes
import os

import spotdl
from spotdl import internals


_LOG_LEVELS_STR = ["INFO", "WARNING", "ERROR", "DEBUG"]

default_conf = {
    "spotify-downloader": {
        "no-remove-original": False,
        "manual": False,
        "no-metadata": False,
        "no-fallback-metadata": False,
        "avconv": False,
        "overwrite": "prompt",
        "input-ext": ".m4a",
        "output-ext": ".mp3",
        "write-to": None,
        "trim-silence": False,
        "download-only-metadata": False,
        "dry-run": False,
        "music-videos-only": False,
        "no-spaces": False,
        "file-format": "{artist} - {track_name}",
        "search-format": "{artist} - {track_name} lyrics",
        "youtube-api-key": None,
        "skip": None,
        "write-successful": None,
        "log-level": "INFO",
        "spotify_client_id": "4fe3fecfe5334023a1472516cc99d805",
        "spotify_client_secret": "0f02b7c483c04257984695007a4a8d5c",
    }
}


def log_leveller(log_level_str):
    loggin_levels = [logging.INFO, logging.WARNING, logging.ERROR, logging.DEBUG]
    log_level_str_index = _LOG_LEVELS_STR.index(log_level_str)
    loggin_level = loggin_levels[log_level_str_index]
    return loggin_level


def merge(default, config):
    """ Override default dict with config dict. """
    merged = default.copy()
    merged.update(config)
    return merged


def get_config(config_file):
    try:
        with open(config_file, "r") as ymlfile:
            cfg = yaml.safe_load(ymlfile)
    except FileNotFoundError:
        log.info("Writing default configuration to {0}:".format(config_file))
        with open(config_file, "w") as ymlfile:
            yaml.dump(default_conf, ymlfile, default_flow_style=False)
            cfg = default_conf

        for line in yaml.dump(
            default_conf["spotify-downloader"], default_flow_style=False
        ).split("\n"):
            if line.strip():
                log.info(line.strip())
        log.info(
            "Please note that command line arguments have higher priority "
            "than their equivalents in the configuration file"
        )

    return cfg["spotify-downloader"]


def override_config(config_file, parser, raw_args=None):
    """ Override default dict with config dict passed as comamnd line argument. """
    config_file = os.path.realpath(config_file)
    config = merge(default_conf["spotify-downloader"], get_config(config_file))
    parser.set_defaults(**config)
    return parser.parse_args(raw_args)


def get_arguments(raw_args=None, to_group=True, to_merge=True):
    parser = argparse.ArgumentParser(
        description="Download and convert tracks from Spotify, Youtube etc.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    if to_merge:
        config_dir = os.path.join(appdirs.user_config_dir(), "spotdl")
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, "config.yml")
        config = merge(default_conf["spotify-downloader"], get_config(config_file))
    else:
        config = default_conf["spotify-downloader"]

    parser.add_argument(
        "-ll",
        "--log-level",
        default=config["log-level"],
        choices=_LOG_LEVELS_STR,
        type=str.upper,
        help="set log verbosity",
    )
    parser.add_argument(
        "-c", "--config", default=None, help="path to custom config.yml file"
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s {}".format(spotdl.__version__),
    )
    parser.add_argument(
        "-f",
        "--file",
        default=None
        )

    parsed = parser.parse_args(raw_args)

    parsed.log_level = log_leveller(parsed.log_level)

    return parsed
