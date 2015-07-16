from os import environ
from os.path import exists, join

import xdg.BaseDirectory
from configparser import ConfigParser


def load_config():
    custom_path = environ.get('TODOMAN_CONFIG')
    if custom_path:
        return _load_config_impl(custom_path)

    for d in xdg.BaseDirectory.xdg_config_dirs:
        path = join(d, 'todoman', 'todoman.conf')
        if exists(path):
            return _load_config_impl(path)

    raise Exception("No configuration file found")


def _load_config_impl(path):
    config = ConfigParser(interpolation=None)
    config.read(path)
    return config
