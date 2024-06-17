from __future__ import annotations

import functools
import glob
import locale
import sys
from contextlib import contextmanager
from datetime import date
from datetime import timedelta
from os.path import isdir
from typing import Callable
from typing import Iterator
from typing import Literal
from typing import ParamSpec
from typing import TypeVar

import click
import click_log

from todoman import exceptions
from todoman import formatters
from todoman.configuration import ConfigurationError
from todoman.configuration import load_config
from todoman.interactive import TodoEditor
from todoman.model import Database
from todoman.model import Todo
from todoman.model import TodoList
from todoman.model import cached_property

click_log.basic_config()


@contextmanager
def handle_error() -> Iterator[None]:
    try:
        yield
    except exceptions.TodomanError as e:
        click.echo(e)
        sys.exit(e.EXIT_CODE)


_T = TypeVar("_T")
_P = ParamSpec("_P")


def catch_errors(f: Callable[_P, _T]) -> Callable[_P, _T]:
    @functools.wraps(f)
    def wrapper(*a, **kw) -> _T:
        with handle_error():
            return f(*a, **kw)

    return wrapper


TODO_ID_MIN = 1
with_id_arg = click.argument("id", type=click.IntRange(min=TODO_ID_MIN))


def _validate_lists_param(
    ctx: click.Context,
    param: click.Parameter,
    lists: list[str],
) -> list[TodoList]:
    return [_validate_list_param(ctx, param, name=list_) for list_ in lists]


def _validate_list_param(
    click_ctx: click.Context,
    param: click.Parameter,
    name: str,
) -> TodoList:
    ctx = click_ctx.find_object(AppContext)
    assert ctx, "AppContext must be defined"
    if name is None:
        if ctx.config["default_list"]:
            name = ctx.config["default_list"]
        else:
            raise click.BadParameter("You must set `default_list` or use -l.")
    lists = {list_.name: list_ for list_ in ctx.db.lists()}
    fuzzy_matches = [
        list_ for list_ in lists.values() if list_.name.lower() == name.lower()
    ]

    if len(fuzzy_matches) == 1:
        return fuzzy_matches[0]

    # case-insensitive matching collides or does not find a result,
    # use exact matching
    if name in lists:
        return lists[name]
    raise click.BadParameter(
        "{}. Available lists are: {}".format(
            name, ", ".join(list_.name for list_ in lists.values())
        )
    )


def _validate_date_param(
    click_ctx: click.Context,
    param: click.Parameter,
    val: str,
) -> date | None:
    ctx = click_ctx.find_object(AppContext)
    assert ctx, "AppContext must be defined"
    try:
        return ctx.formatter.parse_datetime(val)
    except ValueError as e:
        raise click.BadParameter(str(e)) from None


def _validate_categories_param(
    click_ctx: click.Context,
    param: click.Parameter,
    val: str,
) -> list[str]:
    ctx = click_ctx.find_object(AppContext)
    assert ctx, "AppContext must be defined"
    return ctx.formatter.parse_categories(val)


def _validate_priority_param(
    click_ctx: click.Context,
    param: click.Parameter,
    val: str,
) -> int | None:
    ctx = click_ctx.find_object(AppContext)
    assert ctx, "AppContext must be defined"
    try:
        return ctx.formatter.parse_priority(val)
    except ValueError as e:
        raise click.BadParameter(str(e)) from None


def _validate_start_date_param(
    click_ctx: click.Context,
    param: click.Parameter,
    val: str,
) -> tuple[bool, date] | None:
    ctx = click_ctx.find_object(AppContext)
    assert ctx, "AppContext must be defined"
    if not val:
        return None

    if len(val) != 2 or val[0] not in ["before", "after"]:
        raise click.BadParameter("Format should be '[before|after] [DATE]'")

    is_before = val[0] == "before"

    try:
        dt = ctx.formatter.parse_datetime(val[1])
        if dt is None:
            return None
        return is_before, dt
    except ValueError as e:
        raise click.BadParameter(str(e)) from None


def _validate_startable_param(
    click_ctx: click.Context,
    param: click.Parameter,
    val: bool,
) -> bool:
    ctx = click_ctx.find_object(AppContext)
    assert ctx, "AppContext must be defined"
    return val or ctx.config["startable"]


def _validate_todos(
    click_ctx: click.Context,
    param: click.Parameter,
    val: list[int],
) -> list[Todo]:
    ctx = click_ctx.find_object(AppContext)
    assert ctx, "AppContext must be defined"
    with handle_error():
        return [ctx.db.todo(int(id)) for id in val]


def _sort_callback(ctx: click.Context, param: click.Parameter, val: str) -> list[str]:
    fields = val.split(",") if val else []
    for field in fields:
        if field.startswith("-"):
            field = field[1:]

        if field not in Todo.ALL_SUPPORTED_FIELDS and field != "id":
            raise click.BadParameter(f"Unknown field '{field}'")

    return fields


def validate_status(ctx: AppContext, param: click.Parameter, val: str) -> str:
    statuses = val.upper().split(",")

    if "ANY" in statuses:
        return ",".join(Todo.VALID_STATUSES)

    for status in statuses:
        if status not in Todo.VALID_STATUSES:
            raise click.BadParameter(
                'Invalid status, "{}", statuses must be one of "{}", or "ANY"'.format(
                    status, ", ".join(Todo.VALID_STATUSES)
                )
            )

    return val


def _todo_property_options(command: Callable) -> Callable:
    click.option(
        "--category",
        "-c",
        multiple=True,
        default=(),
        callback=_validate_categories_param,
        help="Task categories. Can be used multiple times.",
    )(command)
    click.option(
        "--priority",
        default="",
        callback=_validate_priority_param,
        help="Priority for this task",
    )(command)
    click.option("--location", help="The location where this todo takes place.")(
        command
    )
    click.option(
        "--due",
        "-d",
        default="",
        callback=_validate_date_param,
        help=("Due date of the task, in the format specified in the configuration."),
    )(command)
    click.option(
        "--start",
        "-s",
        default="",
        callback=_validate_date_param,
        help="When the task starts.",
    )(command)

    @functools.wraps(command)
    def command_wrap(*a, **kw) -> click.Command:
        kw["todo_properties"] = {
            key: kw.pop(key) for key in ("due", "start", "location", "priority")
        }
        # longform is singular since user can pass it multiple times, but
        # in actuality it's plural, so manually changing for #cache.todos.
        kw["todo_properties"]["categories"] = kw.pop("category")

        return command(*a, **kw)

    return command_wrap


class AppContext:
    config: dict  # TODO: better typing
    db: Database
    formatter_class: type[formatters.Formatter]

    @cached_property
    def ui_formatter(self) -> formatters.Formatter:
        return formatters.DefaultFormatter(
            self.config["date_format"],
            self.config["time_format"],
            self.config["dt_separator"],
        )

    @cached_property
    def formatter(self) -> formatters.Formatter:
        return self.formatter_class(
            self.config["date_format"],
            self.config["time_format"],
            self.config["dt_separator"],
        )


pass_ctx = click.make_pass_decorator(AppContext)

_interactive_option = click.option(
    "--interactive",
    "-i",
    is_flag=True,
    default=None,
    help="Go into interactive mode before saving the task.",
)


@click.group(invoke_without_command=True)
@click_log.simple_verbosity_option()
@click.option(
    "--colour",
    "--color",
    "colour",
    default=None,
    type=click.Choice(["always", "auto", "never"]),
    help=(
        "By default todoman will disable colored output if stdout "
        "is not a TTY (value `auto`). Set to `never` to disable "
        "colored output entirely, or `always` to enable it "
        "regardless."
    ),
)
@click.option(
    "--porcelain",
    is_flag=True,
    help=(
        "Use a JSON format that will "
        "remain stable regardless of configuration or version."
    ),
)
@click.option(
    "--humanize",
    "-h",
    default=None,
    is_flag=True,
    help="Format all dates and times in a human friendly way",
)
@click.option(
    "--config",
    "-c",
    default=None,
    help="The config file to use.",
    envvar="TODOMAN_CONFIG",
    metavar="PATH",
)
@click.pass_context
@click.version_option(prog_name="todoman")
@catch_errors
def cli(
    click_ctx: click.Context,
    colour: Literal["always"] | Literal["auto"] | Literal["never"],
    porcelain: bool,
    humanize: bool,
    config: str,
) -> None:
    ctx = click_ctx.ensure_object(AppContext)
    try:
        ctx.config = load_config(config)
    except ConfigurationError as e:
        raise click.ClickException(e.args[0]) from None

    if porcelain and humanize:
        raise click.ClickException(
            "--porcelain and --humanize cannot be used at the same time."
        )

    if humanize is None:  # False means explicitly disabled
        humanize = ctx.config["humanize"]

    if porcelain:
        ctx.formatter_class = formatters.PorcelainFormatter
    elif humanize:
        ctx.formatter_class = formatters.HumanizedFormatter
    else:
        ctx.formatter_class = formatters.DefaultFormatter

    colour = colour or ctx.config["color"]
    if colour == "always":
        click_ctx.color = True
    elif colour == "never":
        click_ctx.color = False

    paths = [
        path
        for path in glob.iglob(ctx.config["path"])
        if isdir(path) and not path.endswith("__pycache__")
    ]
    if len(paths) == 0:
        raise exceptions.NoListsFoundError(ctx.config["path"])

    ctx.db = Database(paths, ctx.config["cache_path"])

    # Make python actually use LC_TIME, or the user's locale settings
    locale.setlocale(locale.LC_TIME, "")

    if not click_ctx.invoked_subcommand:
        invoke_command(
            click_ctx,
            ctx.config["default_command"],
        )


def invoke_command(click_ctx: click.Context, command: str) -> None:
    name, *raw_args = command.split(" ")
    if name not in cli.commands:
        raise click.ClickException("Invalid setting for [default_command]")
    parser = cli.commands[name].make_parser(click_ctx)
    opts, args, param_order = parser.parse_args(raw_args)
    for param in param_order:
        if param.name:
            opts[param.name] = param.handle_parse_result(click_ctx, opts, args)[0]
    click_ctx.invoke(cli.commands[name], *args, **opts)


@cli.command()
@click.pass_context
def repl(ctx: click.Context) -> None:
    """Start an interactive shell."""
    try:
        from click_repl import repl

        repl(ctx)
    except ImportError as e:
        click.echo(e)
        sys.exit(-1)


@cli.command()
@click.argument("summary", nargs=-1)
@click.option(
    "--list",
    "-l",
    callback=_validate_list_param,
    help="List in which the task will be saved.",
)
@click.option(
    "--read-description",
    "-r",
    is_flag=True,
    default=False,
    help="Read task description from stdin.",
)
@_todo_property_options
@_interactive_option
@pass_ctx
@catch_errors
def new(
    ctx: AppContext,
    summary: str,
    list: TodoList,
    todo_properties: dict,
    read_description: bool,
    interactive: bool,
) -> None:
    """
    Create a new task with SUMMARY.
    """

    todo = Todo(new=True, list=list)

    default_due = ctx.config["default_due"]
    if default_due:
        assert todo.created_at, "create_at must be defined for new Todo"
        todo.due = todo.created_at + timedelta(hours=default_due)

    default_priority = ctx.config["default_priority"]
    if default_priority is not None:
        todo.priority = default_priority

    for key, value in todo_properties.items():
        if value is not None:
            setattr(todo, key, value)
    todo.summary = " ".join(summary)

    if read_description:
        todo.description = "\n".join(sys.stdin)

    if interactive or (not summary and interactive is None):
        ui = TodoEditor(todo, ctx.db.lists(), ctx.ui_formatter)
        ui.edit()
        click.echo()  # work around lines going missing after urwid

    if not todo.summary:
        raise click.UsageError("No SUMMARY specified")

    ctx.db.save(todo)
    click.echo(ctx.formatter.detailed(todo))


@cli.command()
@pass_ctx
@click.option(
    "--raw",
    is_flag=True,
    help=(
        "Open the raw file for editing in $EDITOR.\n"
        "Only use this if you REALLY know what you're doing!"
    ),
)
@_todo_property_options
@_interactive_option
@with_id_arg
@catch_errors
def edit(
    ctx: AppContext,
    id: int,
    todo_properties: dict,
    interactive: bool,
    raw: bool,
) -> None:
    """
    Edit the task with id ID.
    """
    todo = ctx.db.todo(id)
    if raw:
        click.edit(filename=todo.path)
        return
    old_list = todo.list

    changes = False
    for key, value in todo_properties.items():
        if value is not None and value != []:
            changes = True
            setattr(todo, key, value)

    if interactive or (not changes and interactive is None):
        ui = TodoEditor(todo, ctx.db.lists(), ctx.ui_formatter)
        ui.edit()

    # This little dance avoids duplicates when changing the list:
    new_list = todo.list
    assert new_list, "New list cannot be None"
    assert old_list, "Original list cannot be None"
    todo.list = old_list
    ctx.db.save(todo)
    if old_list != new_list:
        ctx.db.move(todo, new_list=new_list, from_list=old_list)
    click.echo(ctx.formatter.detailed(todo))


@cli.command()
@pass_ctx
@with_id_arg
@catch_errors
def show(ctx: AppContext, id: int) -> None:
    """
    Show details about a task.
    """
    todo = ctx.db.todo(id, read_only=True)
    click.echo(ctx.formatter.detailed(todo))


@cli.command()
@pass_ctx
@with_id_arg
@catch_errors
def path(ctx: AppContext, id: int) -> None:
    """Print the path to a task's file."""
    todo = ctx.db.todo(id, read_only=True)
    click.echo(todo.path)


@cli.command()
@pass_ctx
@click.argument(
    "todos",
    nargs=-1,
    required=True,
    type=click.IntRange(0),
    callback=_validate_todos,
)
@catch_errors
def done(ctx: AppContext, todos: list[Todo]) -> None:
    """Mark one or more tasks as done."""
    for todo in todos:
        todo.complete()
        ctx.db.save(todo)
        click.echo(ctx.formatter.detailed(todo))


@cli.command()
@pass_ctx
@click.argument(
    "todos",
    nargs=-1,
    required=True,
    type=click.IntRange(0),
    callback=_validate_todos,
)
@catch_errors
def cancel(ctx: AppContext, todos: list[Todo]) -> None:
    """Cancel one or more tasks."""
    for todo in todos:
        todo.cancel()
        ctx.db.save(todo)
        click.echo(ctx.formatter.detailed(todo))


@cli.command()
@pass_ctx
@click.confirmation_option(prompt="Are you sure you want to delete all done tasks?")
@catch_errors
def flush(ctx: AppContext) -> None:
    """
    Delete done tasks. This will also clear the cache to reset task IDs.
    """
    database = ctx.db
    for todo in database.flush():
        click.echo(ctx.formatter.simple_action("Flushing", todo))


@cli.command()
@pass_ctx
@click.argument("ids", nargs=-1, required=True, type=click.IntRange(0))
@click.option("--yes", is_flag=True, default=False)
@catch_errors
def delete(ctx: AppContext, ids: list[int], yes: bool) -> None:
    """
    Delete tasks.

    Permanently deletes one or more task. It is recommended that you use the
    `cancel` command if you wish to remove this from the pending list, but keep
    the actual task around.
    """

    todos = []
    for i in ids:
        todo = ctx.db.todo(i)
        click.echo(ctx.formatter.compact(todo))
        todos.append(todo)

    if not yes:
        click.confirm("Do you want to delete those tasks?", abort=True)

    for todo in todos:
        click.echo(ctx.formatter.simple_action("Deleting", todo))
        ctx.db.delete(todo)


@cli.command()
@pass_ctx
@click.option(
    "--list", "-l", callback=_validate_list_param, help="The list to copy the tasks to."
)
@click.argument("ids", nargs=-1, required=True, type=click.IntRange(0))
@catch_errors
def copy(ctx: AppContext, list: TodoList, ids: list[int]) -> None:
    """Copy tasks to another list."""

    for id in ids:
        original = ctx.db.todo(id)
        todo = original.clone()
        todo.list = list
        click.echo(ctx.formatter.compact(todo))
        ctx.db.save(todo)


@cli.command()
@pass_ctx
@click.option(
    "--list", "-l", callback=_validate_list_param, help="The list to move the tasks to."
)
@click.argument("ids", nargs=-1, required=True, type=click.IntRange(0))
@catch_errors
def move(ctx: AppContext, list: TodoList, ids: list[int]) -> None:
    """Move tasks to another list."""

    for id in ids:
        todo = ctx.db.todo(id)
        click.echo(ctx.formatter.compact(todo))
        assert todo.list, "Source todo must have a list"
        ctx.db.move(todo, new_list=list, from_list=todo.list)


@cli.command(name="list")
@pass_ctx
@click.argument("lists", nargs=-1, callback=_validate_lists_param)
@click.option("--location", help="Only show tasks with location containg TEXT")
@click.option("--grep", help="Only show tasks with message containg TEXT")
@click.option(
    "--sort",
    help=(
        "Sort tasks using fields like : "
        '"start", "due", "priority", "created_at", "percent_complete" etc.'
        "\nFor all fields please refer to: "
        "<https://todoman.readthedocs.io/en/stable/usage.html> "
    ),
    callback=_sort_callback,
)
@click.option(
    "--reverse/--no-reverse",
    default=True,
    help="Sort tasks in reverse order (see --sort). Defaults to true.",
)
@click.option(
    "--due", default=None, help="Only show tasks due in INTEGER hours", type=int
)
@click.option(
    "--category",
    "-c",
    multiple=True,
    default=(),
    help="Only show tasks with specified categories.",
    callback=_validate_categories_param,
)
@click.option(
    "--priority",
    default=None,
    help=(
        "Only show tasks with priority at least as high as TEXT (low, medium or high)."
    ),
    type=str,
    callback=_validate_priority_param,
)
@click.option(
    "--start",
    default=None,
    callback=_validate_start_date_param,
    nargs=2,
    help="Only shows tasks before/after given DATE",
)
@click.option(
    "--startable",
    default=None,
    is_flag=True,
    callback=_validate_startable_param,
    help=(
        "Show only todos which "
        "should can be started today (i.e.: start time is not in the "
        "future)."
    ),
)
@click.option(
    "--status",
    "-s",
    default="NEEDS-ACTION,IN-PROCESS",
    callback=validate_status,
    help=(
        "Show only todos with the "
        "provided comma-separated statuses. Valid statuses are "
        '"NEEDS-ACTION", "CANCELLED", "COMPLETED", "IN-PROCESS" or "ANY"'
    ),
)
@catch_errors
def list_command(ctx: AppContext, *args, **kwargs) -> None:
    """
    List tasks (default). Filters any completed or cancelled tasks by default.

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
    hide_list = (len(list(ctx.db.lists())) == 1) or (len(kwargs["lists"]) == 1)

    kwargs["categories"] = kwargs.pop("category")

    todos = ctx.db.todos(**kwargs)
    click.echo(ctx.formatter.compact_multiple(todos, hide_list))
