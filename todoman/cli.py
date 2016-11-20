import functools
import glob
import re
from os.path import expanduser, isdir, join

import click

from .configuration import load_config
from .main import dump_idfile, get_task_sort_function, get_todo, get_todos
from .model import Database, Todo
from .ui import EditState, TodoEditor, TodoFormatter

TODO_ID_MIN = 1
with_id_arg = click.argument('id', type=click.IntRange(min=TODO_ID_MIN))


def _validate_lists_param(ctx, param=None, lists=None):
    if lists:
        return [_validate_list_param(ctx, name=l) for l in lists]
    else:
        return ctx.obj['db'].values()


def _validate_list_param(ctx, param=None, name=None):
    if name is None:
        if 'default_list' in ctx.obj['config']['main']:
            name = ctx.obj['config']['main']['default_list']
        else:
            raise click.BadParameter(
                "{}. You must set 'default_list' or use -l."
                .format(name)
            )
    if name in ctx.obj['db']:
        return ctx.obj['db'][name]
    else:
        raise click.BadParameter(
            "{}. Available lists are: {}"
            .format(name, ', '.join(ctx.obj['db']))
        )


def _validate_date_param(ctx, param, val):
    try:
        return ctx.obj['formatter'].unformat_date(val)
    except ValueError as e:
        raise click.BadParameter(e)


def _todo_property_options(command):
    click.option(
        '--due', '-d', default='', callback=_validate_date_param,
        help=('The due date of the task, in the format specified in the '
              'configuration file.'))(command)
    click.option(
        '--start', '-s', default='', callback=_validate_date_param,
        help='When the task starts.')(command)

    @functools.wraps(command)
    def command_wrap(*a, **kw):
        kw['todo_properties'] = {key: kw.pop(key) for key in
                                 ('due', 'start')}
        return command(*a, **kw)

    return command_wrap


_interactive_option = click.option(
    '--interactive', '-i', is_flag=True,
    help='Go into interactive mode before saving the task.')


@click.group(invoke_without_command=True)
@click.option('--human-time/--no-human-time', default=True,
              help=('Accept informal descriptions such as "tomorrow" instead '
                    'of a properly formatted date.'))
@click.option('--colour', '--color', default=None,
              help=('By default todoman will disable colored output if stdout '
                    'is not a TTY (value `auto`). Set to `never` to disable '
                    'colored output entirely, or `always` to enable it '
                    'regardless.'))
@click.pass_context
@click.version_option(prog_name='todoman')
def cli(ctx, human_time, color):
    config = load_config()
    ctx.obj = {}
    ctx.obj['config'] = config
    ctx.obj['formatter'] = TodoFormatter(
        config.get('main', 'date_format', fallback='%Y-%m-%d'),
        human_time
    )
    ctx.obj['db'] = databases = {}

    color = color or ctx.obj['config']['main'].get('color', 'auto')
    if color == 'always':
        ctx.color = True
    elif color == 'never':
        ctx.color = False
    elif color != 'auto':
        raise click.UsageError('Invalid color setting: Choose from always, '
                               'never, auto.')

    for path in glob.iglob(expanduser(config["main"]["path"])):
        if not isdir(path):
            continue
        db = Database(path)
        if databases.setdefault(db.name, db) is not db:
            raise RuntimeError('Detected two databases named {}'
                               .format(db.name))

    if not ctx.invoked_subcommand:
        ctx.invoke(cli.commands["list"])


try:
    import click_repl
    click_repl.register_repl(cli)
    click_repl.register_repl(cli, name="shell")
except ImportError:
    pass


@cli.command()
@click.argument('summary', nargs=-1)
@click.option('--list', '-l', callback=_validate_list_param,
              help='The list to create the task in.')
@_todo_property_options
@_interactive_option
@click.pass_context
def new(ctx, summary, list, todo_properties, interactive):
    '''
    Create a new task with SUMMARY.
    '''

    todo = Todo()
    for key, value in todo_properties.items():
        if value:
            setattr(todo, key, value)
    todo.summary = ' '.join(summary)

    if interactive:
        ui = TodoEditor(todo, ctx.obj['db'].values(), ctx.obj['formatter'])
        if ui.edit() != EditState.saved:
            ctx.exit(1)
        click.echo()  # work around lines going missing after urwid

    if not todo.summary:
        raise click.UsageError('No SUMMARY specified')

    list.save(todo)
    click.echo(ctx.obj['formatter'].detailed(todo, list))


@cli.command()
@click.pass_context
@_todo_property_options
@_interactive_option
@with_id_arg
def edit(ctx, id, todo_properties, interactive):
    '''
    Edit the task with id ID.
    '''
    todo, database = get_todo(ctx.obj['db'], id)
    changes = False
    for key, value in todo_properties.items():
        if value:
            changes = True
            setattr(todo, key, value)

    if interactive:
        ui = TodoEditor(todo, ctx.obj['db'].values(), ctx.obj['formatter'])
        state = ui.edit()
        if state == EditState.saved:
            changes = True

    if changes:
        database.save(todo)
        click.echo(ctx.obj['formatter'].detailed(todo, database))
    else:
        click.echo('No changes.')
        ctx.exit(1)


@cli.command()
@click.pass_context
@with_id_arg
def show(ctx, id):
    '''
    Show details about a task.
    '''
    todo, database = get_todo(ctx.obj['db'], id)
    click.echo(ctx.obj['formatter'].detailed(todo, database))


@cli.command()
@click.pass_context
@click.argument('ids', nargs=-1, required=True, type=click.IntRange(0))
def done(ctx, ids):
    '''
    Mark a task as done.
    '''
    for id in ids:
        todo, database = get_todo(ctx.obj['db'], id)
        todo.is_completed = True
        database.save(todo)
        click.echo(ctx.obj['formatter'].detailed(todo, database))


def _abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@cli.command()
@click.pass_context
@click.confirmation_option(
    prompt='Are you sure you want to delete all done tasks?'
)
def flush(ctx):
    '''
    Delete done tasks.
    '''
    for database in ctx.obj['db'].values():
        for todo in database.todos.values():
            if todo.is_completed:
                click.echo('Deleting {} ({})'.format(todo.uid, todo.summary))
                database.delete(todo)


@cli.command()
@click.pass_context
@click.argument('ids', nargs=-1, required=True, type=click.IntRange(0))
@click.option('--yes', is_flag=True, default=False)
def delete(ctx, ids, yes):
    '''
    Delete tasks.
    '''

    todos, database = get_todos(ctx, ids)

    if not yes:
        click.confirm('Do you want to delete those tasks?', abort=True)

    for todo in todos:
        click.echo('Deleting {} ({})'.format(todo.uid, todo.summary))
        database.delete(todo)


@cli.command()
@click.pass_context
@click.option('--list', '-l', callback=_validate_list_param,
              help='The list to copy the tasks to.')
@click.argument('ids', nargs=-1, required=True, type=click.IntRange(0))
def copy(ctx, list, ids):
    '''
    Copy tasks to another list.
    '''

    todos, database = get_todos(ctx, ids)

    for todo in todos:
        click.echo('Copying {} to {} ({})'.format(
            todo.uid, list, todo.summary))
        list.save(todo)


@cli.command()
@click.pass_context
@click.option('--list', '-l', callback=_validate_list_param,
              help='The list to move the tasks to.')
@click.argument('ids', nargs=-1, required=True, type=click.IntRange(0))
def move(ctx, list, ids):
    '''
    Move tasks to another list.
    '''

    todos, database = get_todos(ctx, ids)

    for todo in todos:
        click.echo('Moving {} to {} ({})'.format(
            todo.uid, list, todo.summary))
        list.save(todo)
        database.delete(todo)


@cli.command()
@click.pass_context
@click.option('--all', '-a', is_flag=True, help='Also show finished tasks.')
@click.argument('lists', nargs=-1, callback=_validate_lists_param)
@click.option('--urgent', is_flag=True, help='Only show urgent tasks.')
@click.option('--location', help='Only show tasks with location containg TEXT')
@click.option('--category', help='Only show tasks with category containg TEXT')
@click.option('--grep', help='Only show tasks with message containg TEXT')
@click.option('--sort', help='Sort tasks using these fields')
@click.option('--reverse/--no-reverse', default=True,
              help='Sort tasks in reverse order (see --sort). '
              'Defaults to true.')
def list(ctx, lists, all, urgent, location, category, grep, sort, reverse):
    """
    List unfinished tasks.

    If no arguments are provided, all lists will be displayed. Otherwise, only
    todos for the specified list will be displayed.

    eg:
      \b
      - `todo list' shows all unfinished tasks from all lists.
      - `todo list work' shows all unfinished tasks from the list `work`.

    This is the default action when running `todo'.
    """

    pattern = re.compile(grep) if grep else None
    # FIXME: When running with no command, this somehow ends up empty:
    lists = lists or ctx.obj['db'].values()
    sort = sort.split(',') if sort else None

    todos = sorted(
        (
            (database, todo)
            for database in lists
            for todo in database.todos.values()
            if (not todo.is_completed or all) and
               (not urgent or todo.priority) and
               (not location or location in todo.location) and
               (not category or category in todo.categories) and
               (not pattern or (
                   pattern.search(todo.summary) or
                   pattern.search(todo.description)
                   ))
        ),
        key=get_task_sort_function(fields=sort),
        reverse=reverse
    )
    ids = {}

    for index, (database, todo) in enumerate(todos, start=TODO_ID_MIN):
        ids[index] = (database.name, todo.filename)
        try:
            click.echo("{:2d} {}".format(
                index,
                ctx.obj['formatter'].compact(todo, database)
            ))
        except Exception as e:
            click.echo("Error while showing {}: {}"
                       .format(join(database.name, todo.filename), e))

    dump_idfile(ids)
