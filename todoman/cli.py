import functools
import glob
import locale
import sys
from datetime import timedelta
from os.path import expanduser, isdir

import click
import click_log

from . import model
from .configuration import ConfigurationException, load_config
from .model import cached_property, Database, FileTodo
from .ui import EditState, PorcelainFormatter, TodoEditor, TodoFormatter

TODO_ID_MIN = 1
with_id_arg = click.argument('id', type=click.IntRange(min=TODO_ID_MIN))


def _validate_lists_param(ctx, param=None, lists=None):
    if lists:
        return [_validate_list_param(ctx, name=l) for l in lists]


def _validate_list_param(ctx, param=None, name=None):
    ctx = ctx.find_object(AppContext)
    if name is None:
        if 'default_list' in ctx.config['main']:
            name = ctx.config['main']['default_list']
        else:
            raise click.BadParameter(
                "{}. You must set 'default_list' or use -l."
                .format(name)
            )
    for l in ctx.db.lists():
        if l.name == name:
            return l
    else:
        list_names = [l.name for l in ctx.db.lists()]
        raise click.BadParameter(
            "{}. Available lists are: {}"
            .format(name, ', '.join(list_names))
        )


def _validate_date_param(ctx, param, val):
    ctx = ctx.find_object(AppContext)
    try:
        return ctx.formatter.parse_datetime(val)
    except ValueError as e:
        raise click.BadParameter(e)


def _validate_priority_param(ctx, param, val):
    ctx = ctx.find_object(AppContext)
    try:
        return ctx.formatter.parse_priority(val)
    except ValueError as e:
        raise click.BadParameter(e)


def _validate_start_date_param(ctx, param, val):
    ctx = ctx.find_object(AppContext)
    if val is None:
        return val
    if val.startswith('before '):
        is_before = True
        val = val[len('before '):]
    elif val.startswith('after '):
        is_before = False
        val = val[len('after '):]
    else:
        raise click.BadParameter(
            "The start date of the task should be"
            "in format '[before|after] <date-format>'")
    try:
        dt = ctx.formatter.parse_datetime(val)
        return is_before, dt
    except ValueError as e:
        raise click.BadParameter(e)


def _sort_callback(ctx, param, val):
    return val.split(',') if val else []


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


class AppContext:
    def __init__(self):
        self.config = None
        self.db = None
        self.porcelain = False

    @cached_property
    def ui_formatter(self):
        return TodoFormatter(
            self.config['main']['date_format'],
            self.config['main']['time_format'],
            self.config['main']['dt_separator']
        )

    @cached_property
    def porcelain_formatter(self):
        return PorcelainFormatter()

    @cached_property
    def formatter(self):
        if self.porcelain:
            return self.porcelain_formatter
        else:
            return self.ui_formatter


pass_ctx = click.make_pass_decorator(AppContext)


_interactive_option = click.option(
    '--interactive', '-i', is_flag=True, default=None,
    help='Go into interactive mode before saving the task.')


@click.group(invoke_without_command=True)
@click_log.init('todoman')
@click_log.simple_verbosity_option()
@click.option('--colour', '--color', default=None,
              type=click.Choice(['always', 'auto', 'never']),
              help=('By default todoman will disable colored output if stdout '
                    'is not a TTY (value `auto`). Set to `never` to disable '
                    'colored output entirely, or `always` to enable it '
                    'regardless.'))
@click.option('--porcelain', is_flag=True, help='Use a JSON format that will '
              'remain stable regardless of configuration or version.')
@click.pass_context
@click.version_option(prog_name='todoman')
def cli(click_ctx, color, porcelain):
    ctx = click_ctx.ensure_object(AppContext)
    try:
        ctx.config = load_config()
    except ConfigurationException as e:
        raise click.ClickException(e.args[0])

    color = color or ctx.config['main']['color']
    if color == 'always':
        click_ctx.color = True
    elif color == 'never':
        click_ctx.color = False

    ctx.porcelain = porcelain

    paths = [
        path for path in glob.iglob(expanduser(ctx.config["main"]["path"]))
        if isdir(path)
    ]
    if len(paths) == 0:
        click.echo("No lists found matching {}, "
                   "create a directory for a new list"
                   .format(ctx.config["main"]["path"]))
        ctx.exit(1)

    ctx.db = Database(paths, ctx.config['main']['cache_path'])

    if not click_ctx.invoked_subcommand:
        click_ctx.invoke(cli.commands["list"])

    # Make python actually use LC_TIME, or the user's locale settings
    locale.setlocale(locale.LC_TIME, "")


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
@pass_ctx
def new(ctx, summary, list, todo_properties, interactive):
    '''
    Create a new task with SUMMARY.
    '''

    todo = FileTodo()

    default_due = ctx.config['main']['default_due']
    if default_due:
        todo.due = todo.created_at + timedelta(hours=default_due)

    for key, value in todo_properties.items():
        if value:
            setattr(todo, key, value)
    todo.summary = ' '.join(summary)

    if interactive or (not summary and interactive is None):
        ui = TodoEditor(todo, ctx.db.lists(), ctx.formatter)
        if ui.edit() != EditState.saved:
            sys.exit(1)
        click.echo()  # work around lines going missing after urwid

    if not todo.summary:
        raise click.UsageError('No SUMMARY specified')

    todo.list = list
    ctx.db.save(todo, list)
    click.echo(ctx.formatter.detailed(todo))


@cli.command()
@pass_ctx
@_todo_property_options
@_interactive_option
@with_id_arg
def edit(ctx, id, todo_properties, interactive):
    '''
    Edit the task with id ID.
    '''
    todo = ctx.db.todo(id)
    old_list = todo.list

    changes = False
    for key, value in todo_properties.items():
        if value:
            changes = True
            setattr(todo, key, value)

    if interactive or (not changes and interactive is None):
        ui = TodoEditor(todo, ctx.db.lists(), ctx.ui_formatter)
        state = ui.edit()
        if state == EditState.saved:
            changes = True

    if changes:
        todo.save()
        if old_list.name != todo.list.name:
            ctx.db.move(todo, todo.list, from_list=old_list)
        click.echo(ctx.formatter.detailed(todo))
    else:
        click.echo('No changes.')
        sys.exit(1)


@cli.command()
@pass_ctx
@with_id_arg
def show(ctx, id):
    '''
    Show details about a task.
    '''
    try:
        todo = ctx.db.todo(id)
        click.echo(ctx.formatter.detailed(todo))
    except model.NoSuchTodo:
        click.echo("No todo with id {}.".format(id))
        sys.exit(-2)


@cli.command()
@pass_ctx
@click.argument('ids', nargs=-1, required=True, type=click.IntRange(0))
def done(ctx, ids):
    '''
    Mark a task as done.
    '''
    for id in ids:
        todo = ctx.db.todo(id)
        todo.is_completed = True
        todo.save()
        click.echo(ctx.formatter.detailed(todo))


def _abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()


@cli.command()
@pass_ctx
@click.confirmation_option(
    prompt='Are you sure you want to delete all done tasks?'
)
def flush(ctx):
    '''
    Delete done tasks. This will also clear the cache to reset task IDs.
    '''
    database = ctx.db
    for todo in database.flush():
        click.echo(ctx.obj['formatter'].simple_action('Flushing', todo))


@cli.command()
@pass_ctx
@click.argument('ids', nargs=-1, required=True, type=click.IntRange(0))
@click.option('--yes', is_flag=True, default=False)
def delete(ctx, ids, yes):
    '''Delete tasks.'''

    todos = []
    for i in ids:
        todo = ctx.db.todo(i)
        click.echo(ctx.formatter.compact(todo))
        todos.append(todo)

    if not yes:
        click.confirm('Do you want to delete those tasks?', abort=True)

    for todo in todos:
        click.echo(ctx.formatter.simple_action('Deleting', todo))
        ctx.db.delete(todo)


@cli.command()
@pass_ctx
@click.option('--list', '-l', callback=_validate_list_param,
              help='The list to copy the tasks to.')
@click.argument('ids', nargs=-1, required=True, type=click.IntRange(0))
def copy(ctx, list, ids):
    '''Copy tasks to another list.'''

    for id in ids:
        todo = ctx.db.todo(id)
        click.echo(ctx.formatter.compact(todo))
        ctx.db.save(todo, list)


@cli.command()
@pass_ctx
@click.option('--list', '-l', callback=_validate_list_param,
              help='The list to move the tasks to.')
@click.argument('ids', nargs=-1, required=True, type=click.IntRange(0))
def move(ctx, list, ids):
    '''Move tasks to another list.'''

    for id in ids:
        todo = ctx.db.todo(id)
        click.echo(ctx.formatter.compact(todo))
        ctx.db.move(todo, list)


@cli.command()
@pass_ctx
@click.option('--all', '-a', is_flag=True, help='Also show finished tasks.')
@click.argument('lists', nargs=-1, callback=_validate_lists_param)
@click.option('--location', help='Only show tasks with location containg TEXT')
@click.option('--category', help='Only show tasks with category containg TEXT')
@click.option('--grep', help='Only show tasks with message containg TEXT')
@click.option('--sort', help='Sort tasks using these fields',
              callback=_sort_callback)
@click.option('--reverse/--no-reverse', default=True,
              help='Sort tasks in reverse order (see --sort). '
              'Defaults to true.')
@click.option('--due', default=None, help='Only show tasks due in DUE hours',
              type=int)
@click.option('--priority', default=None, help='Only show tasks with'
              ' priority at least as high as the specified one', type=str,
              callback=_validate_priority_param)
@click.option('--done-only', default=False, is_flag=True,
              help='Only show finished tasks')
@click.option('--start', default=None, callback=_validate_start_date_param,
              help='Only shows tasks before/after given DATE')
def list(ctx, **kwargs):
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

    todos = ctx.db.todos(**kwargs)
    click.echo(ctx.formatter.compact_multiple(todos))
