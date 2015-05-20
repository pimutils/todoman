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
import glob
from os.path import expanduser, join
import json

from dateutil.tz import tzlocal
from docopt import docopt
import xdg.BaseDirectory

from .model import Database, Todo
from .ui import TodoEditor, TodoFormatter

logging.basicConfig(level=logging.ERROR)

ID_FILE = join(xdg.BaseDirectory.xdg_cache_home, 'todoman', 'ids')


def load_config():
    for d in xdg.BaseDirectory.xdg_config_dirs:
        path = join(d, 'todoman', 'todoman.conf')
        if os.path.exists(path):
            config = ConfigParser(interpolation=None)
            config.read(path)
            return config

    raise Exception("No configuration file found")


def load_idfile():
    try:
        with open(ID_FILE) as f:
            rv = json.load(f)
            if isinstance(rv, dict):
                return rv
    except (OSError, IOError):
        pass

    return {}


def dump_idfile(ids):
    assert isinstance(ids, dict)
    dirname = os.path.dirname(ID_FILE)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    with open(ID_FILE, 'w') as f:
        json.dump(ids, f)


def task_sort_func(todo):
    """
    Auxiliary function used to sort todos.

    We put the most important items on the bottom of the list because the
    terminal scrolls with the output.

    Items with an immediate due date are considered more important that
    those for which we have more time.
    """

    rv = (-todo.priority, todo.is_completed),
    if todo.due:
        rv += 0, todo.due,
    else:
        rv += 1,
    return rv


def main():
    arguments = docopt(__doc__, version='Todoman')  # TODO: Append version

    config = load_config()
    databases = {}
    formatter = TodoFormatter(config["main"]["date_format"])

    for path in glob.iglob(expanduser(config["main"]["path"])):
        databases[path] = Database(path)

    if arguments["ID"]:
        ids = load_idfile()
        if not ids:
            print("List all tasks with `todo` first.")
            sys.exit(1)

        try:
            db_path, todo_filename = ids[arguments["ID"]]
            database = databases[db_path]
            todo = database.todos[todo_filename]
        except KeyError:
            raise
            print("Invalid todo id.")
            sys.exit(-1)

    if arguments["help"] or arguments["-h"] or arguments["--help"]:
        print(__doc__)
    if arguments["--version"]:
        pass  # TODO!
    elif arguments["edit"]:
        ui = TodoEditor(todo, databases.values(), formatter)

        if ui.edit():
            database.save(todo)
    elif arguments["help"]:
        pass
    elif arguments["new"]:
        todo = Todo()
        ui = TodoEditor(todo, databases.values(), formatter)

        if ui.edit():
            database.save(todo)
    elif arguments["show"]:
        print(formatter.detailed(todo))
    elif arguments["done"]:
        todo.is_completed = True
        database.save(todo)
    else:  # "list" or nothing.
        # TODO: skip entries complete over two days ago
        todos = sorted(
            (
                (database, todo)
                for database in databases.values()
                for todo in database.todos.values()
                if not todo.is_completed or (
                    todo.completed_at and
                    todo.completed_at + timedelta(days=7) >=
                    datetime.now(tzlocal())
                )
            ),
            key=lambda x: task_sort_func(x[1]),
            reverse=True
        )
        ids = {}

        for index, (database, todo) in enumerate(todos, start=1):
            ids[index] = (database.path, todo.filename)
            try:
                print("{:2d} {}".format(index, formatter.compact(todo)))
            except Exception as e:
                print("Error while showing {}: {}"
                      .format(join(database.path, todo.filename), e))

        dump_idfile(ids)

if __name__ == "__main__":
    main()
