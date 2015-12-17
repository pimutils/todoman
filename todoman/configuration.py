from os import environ
from os.path import exists, join

import xdg.BaseDirectory
from configparser import ConfigParser
from click import ClickException

from . import __documentation__


def load_config():
    custom_path = environ.get('TODOMAN_CONFIG')
    if custom_path:
        if not exists(custom_path):
            raise Exception(
                "Configuration file %s does not exist" %
                custom_path
            )
        return _load_config_impl(custom_path)

    for d in xdg.BaseDirectory.xdg_config_dirs:
        path = join(d, 'todoman', 'todoman.conf')
        if exists(path):
            return _load_config_impl(path)

    raise ClickException(
        "No configuration file found.\n"
        "For details on the configuration format and a sample file, see\n"
        "{}/configure.html".format(__documentation__)
    )


def _load_config_impl(path):
    config = ConfigParser(interpolation=None)
    config.read(path)
    return config
