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
from os.path import join
import json

import xdg.BaseDirectory


logging.basicConfig(level=logging.ERROR)

ID_FILE = join(xdg.BaseDirectory.xdg_cache_home, 'todoman', 'ids')


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


def get_todo(databases, todo_id):
    if todo_id:
        ids = load_idfile()
        if not ids:
            print("List all tasks with `todo` first.")
            sys.exit(1)

        try:
            db_path, todo_filename = ids[todo_id]
            database = databases[db_path]
            todo = database.todos[todo_filename]
            return todo, database
        except KeyError:
            return None
