import copy
from os import environ
from os.path import exists, join

import pytoml
import xdg.BaseDirectory
from click import ClickException
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from . import __documentation__


schema = {
    'type': 'object',
    'properties': {
        'main': {
            'type': 'object',
            'properties': {
                'color': {'type': 'string'},
                'path': {'type': 'string'},
                'date_format': {'type': 'string'},
                'default_list': {'type': 'string'},
            },
            'required': [
                'path',
            ],
            'additionalProperties': False
        }
    },
    'required': [
        'main',
    ],
    'additionalProperties': False
}


defaults = {
    'main': {
        'color': 'auto',
        'date_format': '%Y-%m-%d',
    }
}


class ConfigurationError(Exception):
    pass


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
    config = copy.deepcopy(defaults)
    with open(path) as conffile:
        explicit = pytoml.loads(conffile.read())
    merge_dicts(config, explicit)
    try:
        validate(config, schema)
    except ValidationError as e:
        message_parts = str(e).split('\n\n')
        message = '{}\n\n{}'.format(message_parts[0], message_parts[2])
        raise ConfigurationError(message) from e
    return config
