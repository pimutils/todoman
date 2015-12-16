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
            return dict(json.load(f))
    except (ValueError, OSError, IOError):
        pass

    return {}


def dump_idfile(ids):
    assert isinstance(ids, dict)
    dirname = os.path.dirname(ID_FILE)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    with open(ID_FILE, 'w') as f:
        json.dump(list(ids.items()), f)


def task_sort_func(todo):
    """
    Auxiliary function used to sort todos.

    We put the most important items on the bottom of the list because the
    terminal scrolls with the output.

    Items with an immediate due date are considered more important that
    those for which we have more time.
    """

    rv = (
        -todo.priority,
        todo.is_completed,
        (todo.due.timestamp() if todo.due else float('inf')),
        (-todo.created_at.timestamp() if todo.created_at else 0),
        todo.uid  # make ordering deterministic, even if it makes no sense
    )
    return rv


def get_todo(databases, todo_id):
    ids = load_idfile()
    if not ids:
        print("List all tasks with `todo` to know the task number.")
        sys.exit(1)

    try:
        db_name, todo_filename = ids[todo_id]
        database = databases[db_name]
        todo = database.todos[todo_filename]
        return todo, database
    except KeyError:
        print("No todo with id {}.".format(todo_id))
        sys.exit(-2)
        # raise ValueError("No such todo {}.".format(todo_id)) from e
