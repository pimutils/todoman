import functools
import glob
import locale
import sys
from contextlib import contextmanager
from datetime import timedelta
from os.path import expanduser, isdir

import click
import click_log

from todoman import exceptions, formatters
from todoman.configuration import ConfigurationException, load_config
from todoman.interactive import TodoEditor
from todoman.model import cached_property, Database, Todo


@contextmanager
def handle_error():
    try:
        yield
    except exceptions.TodomanException as e:
        click.echo(e)
        sys.exit(e.EXIT_CODE)


def catch_errors(f):
    @functools.wraps(f)
    def wrapper(*a, **kw):
        with handle_error():
            return f(*a, **kw)
    return wrapper


TODO_ID_MIN = 1
with_id_arg = click.argument('id', type=click.IntRange(min=TODO_ID_MIN))


def _validate_lists_param(ctx, param=None, lists=None):
    if lists:
        return [_validate_list_param(ctx, name=l) for l in lists]


def _validate_list_param(ctx, param=None, name=None):
    ctx = ctx.find_object(AppContext)
    if name is None:
        if ctx.config['main']['default_list']:
            name = ctx.config['main']['default_list']
        else:
            raise click.BadParameter(
                'You must set "default_list" or use -l.'
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
    if not val:
        return val

    if len(val) != 2 or val[0] not in ['before', 'after']:
        raise click.BadParameter("Format should be '[before|after] [DATE]'")

    is_before = val[0] == 'before'

    try:
        dt = ctx.formatter.parse_datetime(val[1])
        return is_before, dt
    except ValueError as e:
        raise click.BadParameter(e)


def _validate_startable_param(ctx, param, val):
    ctx = ctx.find_object(AppContext)
    return val or ctx.config['main']['startable']


def _validate_todos(ctx, param, val):
    ctx = ctx.find_object(AppContext)
    with handle_error():
        return [ctx.db.todo(int(id)) for id in val]


def _sort_callback(ctx, param, val):
    fields = val.split(',') if val else []
    for field in fields:
        if field.startswith('-'):
            field = field[1:]

        if field not in Todo.ALL_SUPPORTED_FIELDS and field != 'id':
            raise click.BadParameter('Unknown field "{}"'.format(field))

    return fields


def validate_status(ctx=None, param=None, val=None):
    # The default command doesn't run callbacks as expected, so it needs to
    # specify the callback'd type. When `list` is called explicitly, this
    # callback *IS* run, so we need to handle that edge case:
    if not isinstance(val, str):
        return val

    statuses = val.upper().split(',')

    if 'ANY' in statuses:
        return Todo.VALID_STATUSES

    for status in statuses:
        if status not in Todo.VALID_STATUSES:
            raise click.BadParameter(
                'Invalid status, "{}", statuses must be one of "{}", or "ANY"'
                .format(status, ', '.join(Todo.VALID_STATUSES))
            )

    return statuses


def _todo_property_options(command):
    click.option('--location', help=('The location where '
                 'this todo takes place.'))(command)
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
                                 ('due', 'start', 'location')}
        return command(*a, **kw)

    return command_wrap


class AppContext:
    def __init__(self):
        self.config = None
        self.db = None
        self.formatter_class = None

    @cached_property
    def ui_formatter(self):
        return formatters.DefaultFormatter(
            self.config['main']['date_format'],
            self.config['main']['time_format'],
            self.config['main']['dt_separator']
        )

    @cached_property
    def formatter(self):
        return self.formatter_class(
            self.config['main']['date_format'],
            self.config['main']['time_format'],
            self.config['main']['dt_separator']
        )


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
@click.option('--humanize', '-h', default=None, is_flag=True,
              help='Format all dates and times in a human friendly way')
@click.pass_context
@click.version_option(prog_name='todoman')
@catch_errors
def cli(click_ctx, color, porcelain, humanize):
    ctx = click_ctx.ensure_object(AppContext)
    try:
        ctx.config = load_config()
    except ConfigurationException as e:
        raise click.ClickException(e.args[0])

    if porcelain and humanize:
        raise click.ClickException('--porcelain and --humanize cannot be used'
                                   ' at the same time.')

    if humanize is None:  # False means explicitly disabled
        humanize = ctx.config['main']['humanize']

    if humanize:
        ctx.formatter_class = formatters.HumanizedFormatter
    elif porcelain:
        ctx.formatter_class = formatters.PorcelainFormatter
    else:
        ctx.formatter_class = formatters.DefaultFormatter

    color = color or ctx.config['main']['color']
    if color == 'always':
        click_ctx.color = True
    elif color == 'never':
        click_ctx.color = False

    paths = [
        path for path in glob.iglob(expanduser(ctx.config["main"]["path"]))
        if isdir(path)
    ]
    if len(paths) == 0:
        raise exceptions.NoListsFound(ctx.config["main"]["path"])

    ctx.db = Database(paths, ctx.config['main']['cache_path'])

    # Make python actually use LC_TIME, or the user's locale settings
    locale.setlocale(locale.LC_TIME, "")

    if not click_ctx.invoked_subcommand:
        invoke_command(
            click_ctx,
            ctx.config['main']['default_command'],
        )


def invoke_command(click_ctx, command):
    name, *args = command.split(' ')
    if name not in cli.commands:
        raise click.ClickException(
            'Invalid setting for [main][default_command]'
        )
    click_ctx.invoke(cli.commands[command], args)


try:  # pragma: no cover
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
@catch_errors
def new(ctx, summary, list, todo_properties, interactive):
    '''
    Create a new task with SUMMARY.
    '''

    todo = Todo(new=True, list=list)

    default_due = ctx.config['main']['default_due']
    if default_due:
        todo.due = todo.created_at + timedelta(hours=default_due)

    for key, value in todo_properties.items():
        if value:
            setattr(todo, key, value)
    todo.summary = ' '.join(summary)

    if interactive or (not summary and interactive is None):
        ui = TodoEditor(todo, ctx.db.lists(), ctx.ui_formatter)
        ui.edit()
        click.echo()  # work around lines going missing after urwid

    if not todo.summary:
        raise click.UsageError('No SUMMARY specified')

    ctx.db.save(todo)
    click.echo(ctx.formatter.detailed(todo))


@cli.command()
@pass_ctx
@_todo_property_options
@_interactive_option
@with_id_arg
@catch_errors
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
        ui.edit()

    # This little dance avoids duplicates when changing the list:
    new_list = todo.list
    todo.list = old_list
    ctx.db.save(todo)
    if old_list != new_list:
        ctx.db.move(todo, new_list=new_list, from_list=old_list)
    click.echo(ctx.formatter.detailed(todo))


@cli.command()
@pass_ctx
@with_id_arg
@catch_errors
def show(ctx, id):
    '''
    Show details about a task.
    '''
    todo = ctx.db.todo(id, read_only=True)
    click.echo(ctx.formatter.detailed(todo))


@cli.command()
@pass_ctx
@click.argument(
    'todos',
    nargs=-1,
    required=True,
    type=click.IntRange(0),
    callback=_validate_todos,
)
@catch_errors
def done(ctx, todos):
    """Mark one or more tasks as done."""
    for todo in todos:
        todo.complete()
        ctx.db.save(todo)
        click.echo(ctx.formatter.detailed(todo))


@cli.command()
@pass_ctx
@click.argument(
    'todos',
    nargs=-1,
    required=True,
    type=click.IntRange(0),
    callback=_validate_todos,
)
@catch_errors
def cancel(ctx, todos):
    """Cancel one or more tasks."""
    for todo in todos:
        todo.cancel()
        ctx.db.save(todo)
        click.echo(ctx.formatter.detailed(todo))


@cli.command()
@pass_ctx
@click.confirmation_option(
    prompt='Are you sure you want to delete all done tasks?'
)
@catch_errors
def flush(ctx):
    '''
    Delete done tasks. This will also clear the cache to reset task IDs.
    '''
    database = ctx.db
    for todo in database.flush():
        click.echo(ctx.formatter.simple_action('Flushing', todo))


@cli.command()
@pass_ctx
@click.argument('ids', nargs=-1, required=True, type=click.IntRange(0))
@click.option('--yes', is_flag=True, default=False)
@catch_errors
def delete(ctx, ids, yes):
    '''
    Delete tasks.

    Permanently deletes one or more task. It is recommended that you use the
    `cancel` command if you wish to remove this from the pending list, but keep
    the actual task around.
    '''

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
@catch_errors
def copy(ctx, list, ids):
    '''Copy tasks to another list.'''

    for id in ids:
        original = ctx.db.todo(id)
        todo = original.clone()
        todo.list = list
        click.echo(ctx.formatter.compact(todo))
        ctx.db.save(todo)


@cli.command()
@pass_ctx
@click.option('--list', '-l', callback=_validate_list_param,
              help='The list to move the tasks to.')
@click.argument('ids', nargs=-1, required=True, type=click.IntRange(0))
@catch_errors
def move(ctx, list, ids):
    '''Move tasks to another list.'''

    for id in ids:
        todo = ctx.db.todo(id)
        click.echo(ctx.formatter.compact(todo))
        ctx.db.move(todo, list)


@cli.command()
@pass_ctx
@click.argument('lists', nargs=-1, callback=_validate_lists_param)
@click.option('--location', help='Only show tasks with location containg TEXT')
@click.option('--category', help='Only show tasks with category containg TEXT')
@click.option('--grep', help='Only show tasks with message containg TEXT')
@click.option('--sort', help='Sort tasks using these fields',
              callback=_sort_callback)
@click.option('--reverse/--no-reverse', default=True,
              help='Sort tasks in reverse order (see --sort). '
              'Defaults to true.')
@click.option('--due', default=None, help='Only show tasks due in INTEGER '
              'hours', type=int)
@click.option('--priority', default=None, help='Only show tasks with'
              ' priority at least as high as TEXT (low, medium or high).',
              type=str, callback=_validate_priority_param)
@click.option('--start', default=None, callback=_validate_start_date_param,
              nargs=2, help='Only shows tasks before/after given DATE')
@click.option('--startable', default=None, is_flag=True,
              callback=_validate_startable_param, help='Show only todos which '
              'should can be started today (i.e.: start time is not in the '
              'future).')
@click.option('--status', '-s', default=['NEEDS-ACTION', 'IN-PROCESS'],
              callback=validate_status, help='Show only todos with the '
              'provided comma-separated statuses. Valid statuses are '
              '"NEEDS-ACTION", "CANCELLED", "COMPLETED", "IN-PROCESS" or "ANY"'
              )
@catch_errors
def list(ctx, **kwargs):
    """
    List tasks. Filters any completed or cancelled tasks by default.

    If no arguments are provided, all lists will be displayed, and only
    incomplete tasks are show. Otherwise, only todos for the specified list
    will be displayed.

    eg:
      \b
      - `todo list' shows all unfinished tasks from all lists.
      - `todo list work' shows all unfinished tasks from the list `work`.

    This is the default action when running `todo'.

    The following commands can further filter shown todos, or include those
    omited by default:
    """
    todos = ctx.db.todos(**kwargs)
    click.echo(ctx.formatter.compact_multiple(todos))
