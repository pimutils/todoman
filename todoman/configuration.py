from os import environ
from os.path import exists, join

import xdg.BaseDirectory
import toml
from click import ClickException

from . import __documentation__


defaults = {
    'main': {
        'color': 'auto',
        'date_format': '%Y-%m-%d',
    }
}


def merge_dicts(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and k in a:
            merge_dicts(a[k], v)
        else:
            a[k] = v


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
        path = join(d, 'todoman', 'todoman.toml')
        if exists(path):
            return _load_config_impl(path)

    raise ClickException(
        "No configuration file found.\n"
        "For details on the configuration format and a sample file, see\n"
        "{}/configure.html".format(__documentation__)
    )


def _load_config_impl(path):
    with open(path) as conffile:
        config = toml.loads(conffile.read())
    # TODO: Validate required fields here (ie: path)
    merge_dicts(defaults, config)
    return defaults
