from os.path import exists, join

import xdg.BaseDirectory
from configparser import ConfigParser


def load_config():
    for d in xdg.BaseDirectory.xdg_config_dirs:
        path = join(d, 'todoman', 'todoman.conf')
        if exists(path):
            config = ConfigParser(interpolation=None)
            config.read(path)
            return config

    raise Exception("No configuration file found")
