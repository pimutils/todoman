import functools
import glob
import locale
from datetime import timedelta
from os.path import expanduser, isdir

import click
import click_log

from . import model
from .configuration import ConfigurationException, load_config
from .model import Database, FileTodo
from .ui import EditState, PorcelainFormatter, TodoEditor, TodoFormatter

TODO_ID_MIN = 1
with_id_arg = click.argument('id', type=click.IntRange(min=TODO_ID_MIN))


def _validate_lists_param(ctx, param=None, lists=None):
    if lists:
        return [_validate_list_param(ctx, name=l) for l in lists]


def _validate_list_param(ctx, param=None, name=None):
    if name is None:
        if 'default_list' in ctx.obj['config']['main']:
            name = ctx.obj['config']['main']['default_list']
        else:
            raise click.BadParameter(
                "{}. You must set 'default_list' or use -l."
                .format(name)
            )
    for l in ctx.obj['db'].lists():
        if l.name == name:
            return l
    else:
        list_names = [l.name for l in ctx.obj['db'].lists()]
        raise click.BadParameter(
            "{}. Available lists are: {}"
            .format(name, ', '.join(list_names))
        )


def _validate_date_param(ctx, param, val):
    try:
        return ctx.obj['formatter'].parse_datetime(val)
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
def cli(ctx, color, porcelain):
    try:
        config = load_config()
    except ConfigurationException as e:
        raise click.ClickException(e.args[0])

    ctx.obj = {
        'config': config,
    }

    if porcelain:
        ctx.obj['formatter'] = PorcelainFormatter()
    else:
        ctx.obj['formatter'] = TodoFormatter(
            config['main']['date_format'],
            config['main']['time_format'],
            config['main']['dt_separator'],
        )

    color = color or config['main']['color']
    if color == 'always':
        ctx.color = True
    elif color == 'never':
        ctx.color = False

    paths = [
        path for path in glob.iglob(expanduser(config["main"]["path"]))
        if isdir(path)
    ]
    if len(paths) == 0:
        print("list is empty\n")
        print("type - todo --help")

    ctx.obj['db'] = Database(paths, config['main']['cache_path'])

    if not ctx.invoked_subcommand:
        ctx.invoke(cli.commands["list"])

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
@click.pass_context
def new(ctx, summary, list, todo_properties, interactive):
    '''
    Create a new task with SUMMARY.
    '''

    todo = FileTodo()

    default_due = ctx.obj['config']['main']['default_due']
    if default_due:
        todo.due = todo.created_at + timedelta(hours=default_due)

    for key, value in todo_properties.items():
        if value:
            setattr(todo, key, value)
    todo.summary = ' '.join(summary)

    if interactive or (not summary and interactive is None):
        ui = TodoEditor(todo, ctx.obj['db'].lists(), ctx.obj['formatter'])
        if ui.edit() != EditState.saved:
            ctx.exit(1)
        click.echo()  # work around lines going missing after urwid

    if not todo.summary:
        raise click.UsageError('No SUMMARY specified')

    todo.list = list
    ctx.obj['db'].save(todo, list)
    click.echo(ctx.obj['formatter'].detailed(todo))


@cli.command()
@click.pass_context
@_todo_property_options
@_interactive_option
@with_id_arg
def edit(ctx, id, todo_properties, interactive):
    '''
    Edit the task with id ID.
    '''
    database = ctx.obj['db']
    todo = database.todo(id)
    changes = False
    for key, value in todo_properties.items():
        if value:
            changes = True
            setattr(todo, key, value)

    if interactive or (not changes and interactive is None):
        ui = TodoEditor(todo, ctx.obj['db'].lists(), ctx.obj['formatter'])
        state = ui.edit()
        if state == EditState.saved:
            changes = True

    if changes:
        todo.save()
        click.echo(ctx.obj['formatter'].detailed(todo))
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
    try:
        todo = ctx.obj['db'].todo(id)
        click.echo(ctx.obj['formatter'].detailed(todo))
    except model.NoSuchTodo:
        click.echo("No todo with id {}.".format(id))
        ctx.exit(-2)


@cli.command()
@click.pass_context
@click.argument('ids', nargs=-1, required=True, type=click.IntRange(0))
def done(ctx, ids):
    '''
    Mark a task as done.
    '''
    for id in ids:
        database = ctx.obj['db']
        todo = database.todo(id)
        todo.is_completed = True
        todo.save()
        click.echo(ctx.obj['formatter'].detailed(todo))


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
    Delete done tasks. This will also clear the cache to reset task IDs.
    '''
    database = ctx.obj['db']
    for todo in database.flush():
        click.echo('Deleting {} ({})'.format(todo.uid, todo.summary))


@cli.command()
@click.pass_context
@click.argument('ids', nargs=-1, required=True, type=click.IntRange(0))
@click.option('--yes', is_flag=True, default=False)
def delete(ctx, ids, yes):
    '''Delete tasks.'''

    todos = []
    for i in ids:
        todo = ctx.obj['db'].todo(i)
        click.echo(ctx.obj['formatter'].compact(todo))
        todos.append(todo)

    if not yes:
        click.confirm('Do you want to delete those tasks?', abort=True)

    for todo in todos:
        click.echo('Deleting {} ({})'.format(todo.uid, todo.summary))
        ctx.obj['db'].delete(todo)


@cli.command()
@click.pass_context
@click.option('--list', '-l', callback=_validate_list_param,
              help='The list to copy the tasks to.')
@click.argument('ids', nargs=-1, required=True, type=click.IntRange(0))
def copy(ctx, list, ids):
    '''Copy tasks to another list.'''

    for id in ids:
        todo = ctx.obj['db'].todo(id)
        click.echo('Copying {} to {} ({})'.format(
            todo.uid, list, todo.summary
        ))

        ctx.obj['db'].save(todo, list)


@cli.command()
@click.pass_context
@click.option('--list', '-l', callback=_validate_list_param,
              help='The list to move the tasks to.')
@click.argument('ids', nargs=-1, required=True, type=click.IntRange(0))
def move(ctx, list, ids):
    '''Move tasks to another list.'''

    for id in ids:
        todo = ctx.obj['db'].todo(id)
        click.echo('Moving {} to {} ({})'.format(
            todo.uid, list, todo.summary
        ))

        ctx.obj['db'].move(todo, list)


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
@click.option('--due', default=None, help='Only show tasks due in DUE hours',
              type=int)
def list(
    ctx, lists, all, urgent, location, category, grep, sort, reverse, due,
         ):
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

    sort = sort.split(',') if sort else None

    db = ctx.obj['db']
    todos = db.todos(
        due=due,
        all=all,
        category=category,
        grep=grep,
        lists=lists,
        location=location,
        reverse=reverse,
        sort=sort,
        urgent=urgent,
    )

    click.echo(ctx.obj['formatter'].compact_multiple(todos))
