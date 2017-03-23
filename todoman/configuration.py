import os
from os.path import exists, join

import xdg.BaseDirectory
from configobj import ConfigObj, flatten_errors
from validate import Validator, VdtValueError

from todoman import __documentation__


class ConfigurationException(Exception):
    def __init__(self, msg):
        super().__init__((
            '{}\nFor details on the configuration format and a sample file, '
            'see\n{}configure.html'
        ).format(msg, __documentation__))


def expand_path(path):
    """expands `~` as well as variable names"""
    return os.path.expanduser(os.path.expandvars(path))


def validate_cache_path(path):
    if path:
        return expand_path(path)
    else:
        return os.path.join(
            xdg.BaseDirectory.xdg_cache_home,
            'todoman/cache.sqlite3',
        )


def validate_date_format(fmt):
    if any(x in fmt for x in ('%H', '%M', '%S', '%X')):
        raise ConfigurationException(
            'Found time component in `date_format`, please use `time_format` '
            'for that.'
        )
    return fmt


def validate_time_format(fmt):
    if any(x in fmt for x in ('%Y', '%y', '%m', '%d', '%x')):
        raise ConfigurationException(
            'Found date component in `time_format`, please use `date_format` '
            'for that.'
        )
    return fmt


def find_config():
    custom_path = os.environ.get('TODOMAN_CONFIG')
    if custom_path:
        if not exists(custom_path):
            raise ConfigurationException(
                "Configuration file {} does not exist".format(custom_path)
            )
        return custom_path

    for d in xdg.BaseDirectory.xdg_config_dirs:
        path = join(d, 'todoman', 'todoman.conf')
        if exists(path):
            return path

    raise ConfigurationException(
        "No configuration file found.\n\n"
    )


def load_config():
    path = find_config()
    specpath = os.path.join(os.path.dirname(__file__), 'confspec.ini')
    validator = Validator({
        'expand_path': expand_path,
        'cache_path': validate_cache_path,
        'date_format': validate_date_format,
        'time_format': validate_time_format,
    })

    config = ConfigObj(path, configspec=specpath, file_error=True)
    validation = config.validate(validator, preserve_errors=True)

    for section, key, error in flatten_errors(config, validation):
        if not error:
            raise ConfigurationException(
                ('{} is missing from the {} section of the configuration ' +
                 'file').format(key, section)
            )
        if isinstance(error, VdtValueError):
            raise ConfigurationException(
                'Bad {} setting, {}'.format(key, error.args[0])
            )

    return config
