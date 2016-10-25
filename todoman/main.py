import functools
import json
import logging
import os
import sys
from os.path import join

import click
import xdg.BaseDirectory

from . import model

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


def get_task_sort_function(fields):
    if not fields:
        fields = [
            'is_completed',
            '-priority',
            'due',
            '-created_at',
        ]

    for field in fields:
        if not hasattr(model.Todo, field.lstrip('-')):
            raise click.UsageError('Unknown task field: {}'.format(field))

    def sort_func(args):
        """
        Auxiliary function used to sort todos.

        We put the most important items on the bottom of the list because the
        terminal scrolls with the output.

        Items with an immediate due date are considered more important that
        those for which we have more time.
        """
        db, todo = args
        rv = []
        for field in fields:
            field = field.lower()
            neg = field.startswith('-')
            if neg:
                # Remove that '-'
                field = field[1:]

            value = getattr(todo, field)
            if field in ('due', 'created_at', 'completed_at'):
                value = value.timestamp() if value else float('inf')

            if neg:
                # This "negates" the value, whichever type. The lambda is the
                # same as Python 2's `cmp` builtin, but with inverted output
                # (-1 instead of 1 etc).
                value = functools.cmp_to_key(
                    lambda a, b: -((a > b) - (a < b)))(value)

            rv.append(value)

        return rv

    return sort_func


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


def get_todos(ctx, ids):
    todos = []
    for id in ids:
        todo, database = get_todo(ctx.obj['db'], id)
        click.echo(ctx.obj['formatter'].compact(todo, database))
        todos.append(todo)
    return todos, database
