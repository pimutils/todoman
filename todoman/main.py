import logging

import click

logging.basicConfig(level=logging.ERROR)


def get_todos(ctx, ids):
    todos = []
    for id in ids:
        todo, database = get_todo(ctx.obj['db'], id)
        click.echo(ctx.obj['formatter'].compact(todo, database))
        todos.append(todo)
    return todos, database
