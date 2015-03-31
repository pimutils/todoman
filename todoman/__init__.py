#!/usr/bin/python3

"""Todoman.

Usage:
  todo
  todo new
  todo edit ID
  todo show ID
  todo done ID
  todo help | -h | --help
  todo --version

"""

import logging
import os
import sys
from configparser import ConfigParser
from datetime import datetime, timedelta
from os.path import join

from dateutil.tz import tzlocal
from docopt import docopt
import xdg.BaseDirectory

from .model import Database, Todo
from .ui import TodoEditor, TodoFormatter

logging.basicConfig(level=logging.ERROR)


def load_config():
    for d in xdg.BaseDirectory.xdg_config_dirs:
        path = join(join(d, 'todoman'), 'todoman.conf')
        if os.path.exists(path):
            config = ConfigParser(interpolation=None)
            config.read(path)
            return config

    raise Exception("No configuration file found")


def main():
    arguments = docopt(__doc__, version='Todoman')  # TODO: Append version

    config = load_config()
    database = Database(os.path.expanduser(config["main"]["path"]))
    formatter = TodoFormatter(config["main"]["date_format"])

    if arguments["ID"]:
        todo_id = int(arguments["ID"])
        todo = database.get_nth(todo_id)
        if not todo:
            print("Invalid todo id.")
            sys.exit(-1)

    if arguments["help"] or arguments["-h"] or arguments["--help"]:
        print(__doc__)
    if arguments["--version"]:
        pass  # TODO!
    elif arguments["edit"]:
        ui = TodoEditor(todo, formatter)

        if ui.edit():
            database.save(todo)
    elif arguments["help"]:
        pass
    elif arguments["new"]:
        todo = Todo()
        ui = TodoEditor(todo, formatter)

        if ui.edit():
            database.save(todo)
    elif arguments["show"]:
        print(formatter.detailed(todo))
    elif arguments["done"]:
        todo.complete()
        database.save(todo)
    else:  # "list" or nothing.
        # TODO: skip entries complete over two days ago
        for index, todo in enumerate(database.todos):
            try:
                if not todo.is_completed or (
                    todo.completed_at and
                    todo.completed_at + timedelta(days=7) >=
                    datetime.now(tzlocal())
                ):
                    print("{:2d} {}"
                          .format(index + 1, formatter.compact(todo)))
            except Exception as e:
                print("Error while showing {}: {}".format(todo.filename, e))

if __name__ == "__main__":
    main()
