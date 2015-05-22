import glob
from datetime import datetime, timedelta
from os.path import expanduser, join

import click
from dateutil.tz import tzlocal

from .configuration import load_config
from .main import task_sort_func, dump_idfile, get_todo
from .model import Database, Todo
from .ui import TodoFormatter, TodoEditor


with_id_arg = click.argument('id', type=click.IntRange(0))


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    config = load_config()
    ctx.obj = {}
    ctx.obj['config'] = config
    ctx.obj['formatter'] = TodoFormatter(config["main"]["date_format"])
    ctx.obj['db'] = {path: Database(path) for path in
                     glob.iglob(expanduser(config["main"]["path"]))}

    if not ctx.invoked_subcommand:
        ctx.invoke(cli.commands["list"])


@cli.command()
@click.pass_context
def new(ctx):
    database = sorted(ctx.obj['db'].values())[0]  # FIXME: Allow selection!!
    todo = Todo()
    ui = TodoEditor(todo, ctx.obj['db'].values(), ctx.obj['formatter'])

    if ui.edit():
        database.save(todo)


@cli.command()
@click.pass_context
@with_id_arg
def edit(ctx, id):
    todo, database = get_todo(ctx.obj['db'], id)
    ui = TodoEditor(todo, ctx.obj['db'].values(), ctx.obj['formatter'])
    if ui.edit():
        database.save(todo)


@cli.command()
@click.pass_context
@with_id_arg
def show(ctx, id):
    todo = get_todo(ctx.obj['db'], id)[0]
    print(ctx.obj['formatter'].detailed(todo))


@cli.command()
@click.pass_context
@with_id_arg
def done(ctx, id):
    todo, database = get_todo(ctx.obj['db'], id)
    todo.is_completed = True
    database.save(todo)


@cli.command()
@click.pass_context
def list(ctx):
    todos = sorted(
        (
            (database, todo)
            for database in ctx.obj['db'].values()
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
            print("{:2d} {}".format(index, ctx.obj['formatter'].compact(todo)))
        except Exception as e:
            print("Error while showing {}: {}"
                  .format(join(database.path, todo.filename), e))

    dump_idfile(ids)


def run():
    cli()
