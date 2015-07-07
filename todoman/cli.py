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


def _validate_lists_param(ctx, lists):
    if lists:
        databases = []
        for l in set(lists):
            databases.append(_validate_list_param(ctx, l))
        return databases
    else:
        return ctx.obj['db'].values()


def _validate_list_param(ctx, l):
    if l in ctx.obj['db']:
        return ctx.obj['db'][l]
    else:
        raise click.BadParameter(
            "List {} not found, these are the lists found: {}"
            .format(l, ', '.join(ctx.obj['db']))
        )


def _validate_due_param(ctx, s):
    if s:
        return datetime.strptime(s, ctx.obj['config']['main']['date_format'])


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    config = load_config()
    ctx.obj = {}
    ctx.obj['config'] = config
    ctx.obj['formatter'] = TodoFormatter(config["main"]["date_format"])
    ctx.obj['db'] = databases = {}
    for path in glob.iglob(expanduser(config["main"]["path"])):
        db = Database(path)
        if databases.setdefault(db.name, db) is not db:
            raise RuntimeError('Detected two databases named {}'
                               .format(db.name))

    if not ctx.invoked_subcommand:
        ctx.invoke(cli.commands["list"])


@cli.command()
@click.argument('summary', nargs=-1)
@click.option('--list', '-l', help='The list to create the task in.')
@click.option('--due', '-d', default='',
              help=('The due date of the task, in the format specified in the '
                    'configuration file.'))
@click.option('--interactive', '-i', is_flag=True,
              help='Go into interactive mode before saving the task.')
@click.pass_context
def new(ctx, summary, list, due, interactive):
    '''
    Create a new task with SUMMARY.
    '''
    database = _validate_list_param(ctx, list)
    due = _validate_due_param(ctx, due)

    todo = Todo()
    todo.summary = ' '.join(summary)
    todo.due = due

    if interactive:
        ui = TodoEditor(todo, ctx.obj['db'].values(), ctx.obj['formatter'])
        if not ui.edit():
            ctx.exit(1)
        click.echo()  # work around lines going missing after urwid

    if not todo.summary:
        click.echo('Empty summary.', err=True)
        ctx.exit(2)

    database.save(todo)
    print(ctx.obj['formatter'].detailed(todo, database))


@cli.command()
@click.pass_context
@with_id_arg
def edit(ctx, id):
    '''
    Edit a task interactively.
    '''
    todo, database = get_todo(ctx.obj['db'], id)
    ui = TodoEditor(todo, ctx.obj['db'].values(), ctx.obj['formatter'])
    if ui.edit():
        database.save(todo)


@cli.command()
@click.pass_context
@with_id_arg
def show(ctx, id):
    '''
    Show details about a task.
    '''
    todo, database = get_todo(ctx.obj['db'], id)
    print(ctx.obj['formatter'].detailed(todo, database))


@cli.command()
@click.pass_context
@click.argument('ids', nargs=-1, type=click.IntRange(0))
def done(ctx, ids):
    '''
    Mark a task as done.
    '''
    for id in ids:
        todo, database = get_todo(ctx.obj['db'], id)
        todo.is_completed = True
        database.save(todo)


@cli.command()
@click.pass_context
@click.argument('lists', nargs=-1, default=())
def list(ctx, lists):
    """
    List unfinished tasks.

      - `todo list` shows all unfinished tasks from all lists.

      - `todo list work` shows all unfinished tasks from the list `work`.
    """

    lists = _validate_lists_param(ctx, lists)
    todos = sorted(
        (
            (database, todo)
            for database in lists
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
        ids[index] = (database.name, todo.filename)
        try:
            print("{:2d} {}".format(
                index,
                ctx.obj['formatter'].compact(todo, database)
            ))
        except Exception as e:
            print("Error while showing {}: {}"
                  .format(join(database.name, todo.filename), e))

    dump_idfile(ids)


def run():
    cli()
