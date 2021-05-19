import importlib
import os
from os.path import exists
from os.path import join
from typing import Any
from typing import Callable
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union

import xdg.BaseDirectory

from todoman import __documentation__


def expand_path(path):
    """expands `~` as well as variable names"""
    return os.path.expanduser(os.path.expandvars(path))


def validate_cache_path(path):
    path = path.replace("$XDG_CACHE_HOME", xdg.BaseDirectory.xdg_cache_home)
    return expand_path(path)


def validate_date_format(fmt):
    if any(x in fmt for x in ("%H", "%M", "%S", "%X")):
        raise ConfigurationException(
            "Found time component in `date_format`, please use `time_format` for that."
        )
    return fmt


def validate_time_format(fmt):
    if any(x in fmt for x in ("%Y", "%y", "%m", "%d", "%x")):
        raise ConfigurationException(
            "Found date component in `time_format`, please use `date_format` for that."
        )
    return fmt


def validate_color_config(value: str):
    if value not in ["always", "auto", "never"]:
        raise ConfigurationException("Invalid `color` settings.")
    return value


def validate_default_priority(value: int):
    if value and not (0 <= value <= 9):
        raise ConfigurationException("Invalid `default_priority` settings.")
    return value


class ConfigEntry(NamedTuple):
    name: str
    type: Union[Type, Tuple[Type]]
    default: Any
    description: str
    validation: Optional[Callable]


NO_DEFAULT = object()

# A list of tuples (name, type, default, description, validation)
CONFIG_SPEC: List[ConfigEntry] = [
    ConfigEntry(
        "path",
        str,
        NO_DEFAULT,
        """
A glob pattern matching the directories where your todos are located. This
pattern will be expanded, and each matching directory (with any icalendar
files) will be treated as a list.""",
        expand_path,
    ),
    ConfigEntry(
        "color",
        str,
        "auto",
        """
By default todoman will disable colored output if stdout is not a TTY (value
``auto``). Set to ``never`` to disable colored output entirely, or ``always``
to enable it regardless. This can be overridden with the ``--color`` option.
""",
        validate_color_config,
    ),
    ConfigEntry(
        "date_format",
        str,
        "%x",
        """
The date format used both for displaying dates, and parsing input dates. If
this option is not specified the system locale's is used.
""",
        validate_date_format,
    ),
    ConfigEntry(
        "time_format",
        str,
        "%X",
        """
The date format used both for displaying times, and parsing input times.
""",
        validate_time_format,
    ),
    ConfigEntry(
        "dt_separator",
        str,
        " ",
        """
The string used to separate date and time when displaying and parsing.
""",
        None,
    ),
    ConfigEntry(
        "humanize",
        bool,
        False,
        """
If set to true, datetimes will be printed in human friendly formats like
"tomorrow", "in one hour", "3 weeks ago", etc.

If false, datetimes fill be formatted using ``date_format`` and
``time_format``.
""",
        None,
    ),
    ConfigEntry(
        "default_list",
        (str, None.__class__),  # type: ignore
        None,
        """
The default list for adding a todo. If you do not specify this option, you
must use the ``--list`` / ``-l`` option every time you add a todo.
""",
        None,
    ),
    ConfigEntry(
        "default_due",
        int,
        24,
        """
The default difference (in hours) between new todo’s due date and creation
date. If not specified, the value is 24. If set to 0, the due date for new
todos will not be set.
""",
        None,
    ),
    ConfigEntry(
        "cache_path",
        str,
        "$XDG_CACHE_HOME/todoman/cache.sqlite3",
        """
The location of the cache file (an sqlite database). This file is used to
store todo data and speed up execution/startup, and also contains the IDs for
todos.
If the value is not specified, a path relative to ``$XDG_CACHE_HOME`` will be used.
``$XDG_CACHE_HOME`` generally resolves to ``~/.cache/``.
""",
        validate_cache_path,
    ),
    ConfigEntry(
        "startable",
        bool,
        False,
        """
If set to true, only show todos which are currently startable; these are
todos which have a start date today, or some day in the past.  Todos with no
start date are always considered current. Incomplete todos (eg:
partially-complete) are also included.
""",
        None,
    ),
    ConfigEntry(
        "default_command",
        str,
        "list",
        """
When running ``todo`` with no commands, run this command.
""",
        None,
    ),
    ConfigEntry(
        "default_priority",
        (int, None.__class__),  # type: ignore
        None,
        """
The default priority of a task on creation.
Highest priority is 1, lowest priority is 10, and 0 means no priority at all.
""",
        validate_default_priority,
    ),
]


class ConfigurationException(Exception):
    def __init__(self, msg):
        super().__init__(
            (
                "{}\nFor details on the configuration format and a sample file, "
                "see\n{}configure.html"
            ).format(msg, __documentation__)
        )


def find_config(custom_path=None):
    if custom_path:
        if not exists(custom_path):
            raise ConfigurationException(
                f"Configuration file {custom_path} does not exist"
            )
        return custom_path

    for d in xdg.BaseDirectory.xdg_config_dirs:
        path = join(d, "todoman", "config.py")
        if exists(path):
            return path

    raise ConfigurationException("No configuration file found.\n\n")


def load_config(custom_path=None):
    path = find_config(custom_path)
    spec = importlib.util.spec_from_file_location("config", path)
    config_source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_source)

    # TODO: Handle SyntaxError

    config = {}
    for name, type_, default, _description, validation in CONFIG_SPEC:
        value = getattr(config_source, name, default)
        if value == NO_DEFAULT:
            raise ConfigurationException(f"Missing '{name}' setting.")
        if not isinstance(value, type_):
            expected = type_.__name__
            actual = value.__class__.__name__
            raise ConfigurationException(
                f"Bad {name} setting. Invalid type "
                f"(expected {expected}, got {actual})."
            )
        if validation:
            value = validation(value)
        config[name] = value

    return config
