import datetime
import sys
from os.path import exists
from unittest import mock
from unittest.mock import call
from unittest.mock import patch
from uuid import uuid4

import click
import hypothesis.strategies as st
import pytest
from dateutil.tz import tzlocal
from freezegun import freeze_time
from hypothesis import given

from tests.helpers import fs_case_sensitive
from tests.helpers import pyicu_sensitive
from todoman.cli import cli
from todoman.cli import exceptions
from todoman.model import Database
from todoman.model import Todo

# TODO: test --grep


def test_list(tmpdir, runner, create):
    result = runner.invoke(cli, ["list"], catch_exceptions=False)
    assert not result.exception
    assert not result.output.strip()

    create("test.ics", f"UID:{uuid4()}\nSUMMARY:harhar\n")
    result = runner.invoke(cli, ["list"])
    assert not result.exception
    assert "harhar" in result.output


def test_no_default_list(runner):
    result = runner.invoke(cli, ["new", "Configure a default list"])

    assert result.exception
    assert (
        "Error: Invalid value for '--list' / '-l': You must set "
        "`default_list` or use -l." in result.output
    )


def test_no_extra_whitespace(tmpdir, runner, create):
    """
    Test that we don't output extra whitespace

    Test that we don't output a lot of extra whitespace when there are no
    tasks, or when there are tasks (eg: both scenarios).

    Note: Other tests should be set up so that comparisons don't care much
    about whitespace, so that if this changes, only this test should fail.
    """
    result = runner.invoke(cli, ["list"], catch_exceptions=False)
    assert not result.exception
    assert result.output == "\n"

    create("test.ics", f"UID:{uuid4()}\nSUMMARY:harhar\n")
    result = runner.invoke(cli, ["list"])
    assert not result.exception
    assert len(result.output.splitlines()) == 1


def test_percent(tmpdir, runner, create):
    create("test.ics", f"UID:{uuid4()}\nSUMMARY:harhar\nPERCENT-COMPLETE:78\n")
    result = runner.invoke(cli, ["list"])
    assert not result.exception
    assert "78%" in result.output


@fs_case_sensitive
@pytest.mark.parametrize("list_name", ["default", "DEfault", "deFAUlT"])
def test_list_case_insensitive(tmpdir, runner, create, list_name):
    result = runner.invoke(cli, ["list", list_name])
    assert not result.exception


@fs_case_sensitive
def test_list_case_insensitive_collision(tmpdir, runner, create):
    """
    Test that the case-insensitive list name matching is not used if
    colliding list names exist.
    """
    tmpdir.mkdir("DEFaUlT")

    result = runner.invoke(cli, ["list", "deFaulT"])
    assert result.exception

    result = runner.invoke(cli, ["list", "default"])
    assert not result.exception

    result = runner.invoke(cli, ["list", "DEFaUlT"])
    assert not result.exception


@fs_case_sensitive
def test_list_case_insensitive_other_collision(tmpdir, runner, create):
    """
    Test that the case-insensitive list name matching is used if a
    collision exists that does not affect the queried list.
    """
    tmpdir.mkdir("coLLiding")
    tmpdir.mkdir("COLLiDING")

    result = runner.invoke(cli, ["list", "cOlliDInG"])
    assert result.exception

    result = runner.invoke(cli, ["list", "DEfAult"])
    assert not result.exception


def test_list_inexistant(tmpdir, runner, create):
    result = runner.invoke(cli, ["list", "nonexistant"])
    assert result.exception
    assert "Error: Invalid value for '[LISTS]...': nonexistant" in result.output

    result = runner.invoke(cli, ["list", "NONexistant"])
    assert result.exception
    assert "Error: Invalid value for '[LISTS]...': NONexistant" in result.output


def test_show_existing(tmpdir, runner, create):
    create(
        "test.ics", f"UID:{uuid4()}\nSUMMARY:harhar\nDESCRIPTION:Lots of text. Yum!\n"
    )
    result = runner.invoke(cli, ["list"])
    result = runner.invoke(cli, ["show", "1"])
    assert not result.exception
    assert "harhar" in result.output
    assert "Lots of text. Yum!" in result.output


def test_show_inexistant(tmpdir, runner, create):
    create("test.ics", f"UID:{uuid4()}\nSUMMARY:harhar\n")
    result = runner.invoke(cli, ["list"])
    result = runner.invoke(cli, ["show", "2"])
    assert result.exit_code == 20
    assert result.output == "No todo with id 2.\n"


def test_human(runner):
    result = runner.invoke(
        cli, ["new", "-l", "default", "-d", "tomorrow", "hail belzebub"]
    )
    assert not result.exception
    assert "belzebub" in result.output

    result = runner.invoke(cli, ["list"])
    assert not result.exception
    assert "belzebub" in result.output


@pytest.mark.xfail(reason="issue#9")
def test_two_events(tmpdir, runner):
    tmpdir.join("default/test.ics").write(
        "BEGIN:VCALENDAR\n"
        "BEGIN:VTODO\n"
        "SUMMARY:task one\n"
        "END:VTODO\n"
        "BEGIN:VTODO\n"
        "SUMMARY:task two\n"
        "END:VTODO\n"
        "END:VCALENDAR"
    )
    result = runner.invoke(cli, ["list"])
    assert not result.exception
    assert len(result.output.splitlines()) == 2
    assert "task one" in result.output
    assert "task two" in result.output


def test_default_command(tmpdir, runner, create):
    create("test.ics", f"UID:{uuid4()}\nSUMMARY:harhar\n")
    result = runner.invoke(cli)
    assert not result.exception
    assert "harhar" in result.output


def test_delete(runner, create):
    create("test.ics", f"UID:{uuid4()}\nSUMMARY:harhar\n")
    result = runner.invoke(cli, ["list"])
    assert not result.exception
    result = runner.invoke(cli, ["delete", "1", "--yes"])
    assert not result.exception
    result = runner.invoke(cli, ["list"])
    assert not result.exception
    assert not result.output.strip()


def test_delete_prompt(todo_factory, runner, todos):
    todo_factory()

    result = runner.invoke(cli, ["delete", "1"], input="yes")

    assert not result.exception
    assert '[y/N]: yes\nDeleting "YARR!"' in result.output

    assert len(list(todos())) == 0


def test_copy(tmpdir, runner, create):
    tmpdir.mkdir("other_list")
    create("test.ics", f"UID:{uuid4()}\nSUMMARY:test_copy\n")
    result = runner.invoke(cli, ["list"])
    assert not result.exception
    assert "test_copy" in result.output
    assert "default" in result.output
    assert "other_list" not in result.output
    result = runner.invoke(cli, ["copy", "-l", "other_list", "1"])
    assert not result.exception
    result = runner.invoke(cli, ["list"])
    assert not result.exception
    assert "test_copy" in result.output
    assert "default" in result.output
    assert "other_list" in result.output


def test_move(tmpdir, runner, create):
    tmpdir.mkdir("other_list")
    create("test.ics", f"UID:{uuid4()}\nSUMMARY:test_move\n")
    result = runner.invoke(cli, ["list"])
    assert not result.exception
    assert "test_move" in result.output
    assert "default" in result.output
    assert "other_list" not in result.output
    result = runner.invoke(cli, ["move", "-l", "other_list", "1"])
    assert not result.exception
    result = runner.invoke(cli, ["list"])
    assert not result.exception
    assert "test_move" in result.output
    assert "default" not in result.output
    assert "other_list" in result.output


@pyicu_sensitive
@freeze_time("2017-03-17 20:22:19")
def test_dtstamp(tmpdir, runner, create):
    """Test that we add the DTSTAMP to new entries as per RFC5545."""
    result = runner.invoke(cli, ["new", "-l", "default", "test event"])
    assert not result.exception

    db = Database([tmpdir.join("default")], tmpdir.join("/dtstamp_cache"))
    todo = list(db.todos())[0]
    assert todo.dtstamp is not None
    assert todo.dtstamp == datetime.datetime.now(tz=tzlocal())


def test_default_list(tmpdir, runner, create, config):
    """Test the default_list config parameter"""
    result = runner.invoke(cli, ["new", "test default list"])
    assert result.exception

    config.write('default_list = "default"\n', "a")

    result = runner.invoke(cli, ["new", "test default list"])
    assert not result.exception

    db = Database([tmpdir.join("default")], tmpdir.join("/default_list"))
    todo = list(db.todos())[0]
    assert todo.summary == "test default list"


@pytest.mark.parametrize(
    ("default_due", "expected_due_hours"),
    [(None, 24), (1, 1), (0, None)],
    ids=["not specified", "greater than 0", "0"],
)
def test_default_due(tmpdir, runner, create, default_due, expected_due_hours, config):
    """Test setting the due date using the default_due config parameter"""
    if default_due is not None:
        config.write(f"default_due = {default_due}\n", "a")

    runner.invoke(cli, ["new", "-l", "default", "aaa"])
    db = Database([tmpdir.join("default")], tmpdir.join("/default_list"))
    todo = list(db.todos())[0]

    if expected_due_hours is None:
        assert todo.due is None
    else:
        assert (todo.due - todo.created_at) == datetime.timedelta(
            hours=expected_due_hours
        )


@pyicu_sensitive
@freeze_time(datetime.datetime.now())
def test_default_due2(tmpdir, runner, create, todos, config):
    config.write("default_due = 24\n", "a")

    r = runner.invoke(cli, ["new", "-ldefault", "-dtomorrow", "aaa"])
    assert not r.exception
    r = runner.invoke(cli, ["new", "-ldefault", "bbb"])
    assert not r.exception
    r = runner.invoke(cli, ["new", "-ldefault", "-d", "one hour", "ccc"])
    assert not r.exception

    todos = {t.summary: t for t in todos(status="ANY")}
    assert todos["aaa"].due.date() == todos["bbb"].due.date()
    assert todos["ccc"].due == todos["bbb"].due - datetime.timedelta(hours=23)


def test_sorting_fields(tmpdir, runner, default_database):
    tasks = []
    for i in range(1, 10):
        days = datetime.timedelta(days=i)

        todo = Todo(new=True)
        todo.list = next(default_database.lists())
        todo.due = datetime.datetime.now() + days
        todo.created_at = datetime.datetime.now() - days
        todo.summary = f"harhar{i}"
        tasks.append(todo)

        default_database.save(todo)

    fields = (
        "id",
        "uid",
        "summary",
        "due",
        "priority",
        "created_at",
        "completed_at",
        "dtstamp",
        "status",
        "description",
        "location",
        "categories",
    )

    @given(
        sort_key=st.lists(
            st.sampled_from(fields + tuple("-" + x for x in fields)), unique=True
        )
    )
    def run_test(sort_key):
        sort_key = ",".join(sort_key)
        result = runner.invoke(cli, ["list", "--sort", sort_key])
        assert not result.exception
        assert result.exit_code == 0
        assert len(result.output.strip().splitlines()) == len(tasks)

    run_test()


def test_sorting_output(tmpdir, runner, create):
    create(
        "test.ics",
        f"UID:{uuid4()}\nSUMMARY:aaa\n"
        "DUE;VALUE=DATE-TIME;TZID=ART:20160102T000000\n",
    )
    create(
        "test2.ics",
        f"UID:{uuid4()}\nSUMMARY:bbb\n"
        "DUE;VALUE=DATE-TIME;TZID=ART:20160101T000000\n",
    )

    examples = [("-summary", ["aaa", "bbb"]), ("due", ["aaa", "bbb"])]

    # Normal sorting, reversed by default
    all_examples = [(["--sort", key], order) for key, order in examples]

    # Testing --reverse, same exact output
    all_examples.extend(
        (["--reverse", "--sort", key], order) for key, order in examples
    )

    # Testing --no-reverse
    all_examples.extend(
        (["--no-reverse", "--sort", key], reversed(order)) for key, order in examples
    )

    for args, order in all_examples:
        result = runner.invoke(cli, ["list"] + args)
        assert not result.exception
        lines = result.output.splitlines()
        for i, task in enumerate(order):
            assert task in lines[i]


def test_sorting_null_values(tmpdir, runner, create):
    create("test.ics", f"UID:{uuid4()}\nSUMMARY:aaa\nPRIORITY:9\n")
    create(
        "test2.ics",
        f"UID:{uuid4()}\nSUMMARY:bbb\n"
        "DUE;VALUE=DATE-TIME;TZID=ART:20160101T000000\n",
    )

    result = runner.invoke(cli)
    assert not result.exception
    assert "bbb" in result.output.splitlines()[0]
    assert "aaa" in result.output.splitlines()[1]


def test_sort_invalid_fields(runner):
    result = runner.invoke(cli, ["list", "--sort", "hats"])

    assert result.exception
    assert "Invalid value for '--sort': Unknown field 'hats'" in result.output


@pytest.mark.parametrize("hours", [72, -72])
def test_color_due_dates(tmpdir, runner, create, hours):
    due = datetime.datetime.now() + datetime.timedelta(hours=hours)
    create(
        "test.ics",
        "SUMMARY:aaa\nSTATUS:IN-PROCESS\nDUE;VALUE=DATE-TIME;TZID=ART:{}\n".format(
            due.strftime("%Y%m%dT%H%M%S")
        ),
    )

    result = runner.invoke(cli, ["--color", "always"])
    assert not result.exception
    due_str = due.strftime("%Y-%m-%d")
    if hours == 72:
        expected = (
            f"[ ] 1 \x1b[35m\x1b[0m \x1b[37m{due_str}\x1b[0m aaa @default\x1b[0m\n"
        )
    else:
        expected = (
            f"[ ] 1 \x1b[35m\x1b[0m \x1b[31m{due_str}\x1b[0m aaa @default\x1b[0m\n"
        )
    assert result.output == expected


def test_color_flag(runner, todo_factory):
    todo_factory(due=datetime.datetime(2007, 3, 22))

    result = runner.invoke(cli, ["--color", "always"], color=True)
    assert (
        result.output.strip()
        == "[ ] 1 \x1b[35m\x1b[0m \x1b[31m2007-03-22\x1b[0m YARR! @default\x1b[0m"
    )
    result = runner.invoke(cli, color=True)
    assert (
        result.output.strip()
        == "[ ] 1 \x1b[35m\x1b[0m \x1b[31m2007-03-22\x1b[0m YARR! @default\x1b[0m"
    )

    result = runner.invoke(cli, ["--color", "never"], color=True)
    assert result.output.strip() == "[ ] 1  2007-03-22 YARR! @default"


def test_flush(tmpdir, runner, create, todo_factory, todos):
    todo_factory(summary="aaa", status="COMPLETED")
    todo_factory(summary="bbb")

    all_todos = list(todos(status="ANY"))
    assert len(all_todos) == 2

    result = runner.invoke(cli, ["flush"], input="y\n", catch_exceptions=False)
    assert not result.exception

    all_todos = list(todos(status="ANY"))
    assert len(all_todos) == 1
    assert all_todos[0].summary == "bbb"


def test_edit(runner, default_database, todos):
    todo = Todo(new=True)
    todo.list = next(default_database.lists())
    todo.summary = "Eat paint"
    todo.due = datetime.datetime(2016, 10, 3)
    default_database.save(todo)

    result = runner.invoke(cli, ["edit", "1", "--due", "2017-02-01"])
    assert not result.exception
    assert "2017-02-01" in result.output

    todo = next(todos(status="ANY"))
    assert todo.due == datetime.datetime(2017, 2, 1, tzinfo=tzlocal())
    assert todo.summary == "Eat paint"


def test_edit_move(runner, todo_factory, default_database, tmpdir, todos):
    """
    Test that editing the list in the UI edits the todo as expected

    The goal of this test is not to test the editor itself, but rather the
    `edit` command and its slightly-complex moving logic.
    """
    tmpdir.mkdir("another_list")

    default_database.paths = [
        str(tmpdir.join("default")),
        str(tmpdir.join("another_list")),
    ]
    default_database.update_cache()

    todo_factory(summary="Eat some headphones")

    lists = list(default_database.lists())
    another_list = next(filter(lambda x: x.name == "another_list", lists))

    def moving_edit(self):
        self.current_list = another_list
        self._save_inner()

    with patch("todoman.interactive.TodoEditor.edit", moving_edit):
        result = runner.invoke(cli, ["edit", "1"])

    assert not result.exception

    todos = list(todos())
    assert len(todos) == 1
    assert todos[0].list.name == "another_list"


def test_edit_retains_id(runner, todos, todo_factory):
    """Tests that we retain a todo's ID after editing."""
    original_id = todo_factory().id

    result = runner.invoke(cli, ["edit", "1", "--due", "2017-04-01"])
    assert not result.exception

    todo = next(todos())
    assert todo.due == datetime.datetime(2017, 4, 1, tzinfo=tzlocal())
    assert todo.id == original_id


def test_edit_inexistant(runner):
    """Tests that we show the right output and exit code for inexistant ids."""
    result = runner.invoke(cli, ["edit", "1", "--due", "2017-04-01"])
    assert result.exception
    assert result.exit_code == exceptions.NoSuchTodoError.EXIT_CODE
    assert result.output.strip() == "No todo with id 1."


def test_empty_list(tmpdir, runner, create):
    for item in tmpdir.listdir():
        if item.isdir():
            item.remove()

    result = runner.invoke(cli)
    expected = (
        "No lists found matching {}/*, create a directory for a new list"
    ).format(tmpdir)

    assert expected in result.output


def test_show_location(tmpdir, runner, create):
    create("test.ics", f"UID:{uuid4()}\nSUMMARY:harhar\nLOCATION:Boston\n")

    result = runner.invoke(cli, ["show", "1"])
    assert "Boston" in result.output


def test_location(runner):
    result = runner.invoke(
        cli, ["new", "-l", "default", "--location", "Chembur", "Event Test"]
    )

    assert "Chembur" in result.output


def test_sort_mixed_timezones(runner, create):
    """
    Test sorting mixed timezones.

    The times on this tests are carefully chosen so that a TZ-naive comparison
    gives the opposite results.
    """
    create(
        "test.ics",
        f"UID:{uuid4()}\nSUMMARY:first\nDUE;"
        "VALUE=DATE-TIME;TZID=CET:20170304T180000\n",  # 1700 UTC
    )
    create(
        "test2.ics",
        f"UID:{uuid4()}\nSUMMARY:second\nDUE;"
        "VALUE=DATE-TIME;TZID=HST:20170304T080000\n",  # 1800 UTC
    )

    result = runner.invoke(cli, ["list", "--status", "ANY"])
    assert not result.exception
    output = result.output.strip()
    assert len(output.splitlines()) == 2
    assert "second" in result.output.splitlines()[0]
    assert "first" in result.output.splitlines()[1]


def test_humanize_interactive(runner):
    result = runner.invoke(cli, ["--humanize", "--porcelain", "list"])

    assert result.exception
    assert (
        result.output.strip()
        == "Error: --porcelain and --humanize cannot be used at the same time."
    )


def test_due_bad_date(runner):
    result = runner.invoke(cli, ["new", "--due", "Not a date", "Blargh!"])

    assert result.exception
    assert (
        result.output.strip().splitlines()[-1]
        == "Error: Invalid value for '--due' / '-d': Time description not "
        "recognized: Not a date"
    )


def test_multiple_todos_in_file(runner, create):
    path = create(
        "test.ics", f"UID:{uuid4()}\nSUMMARY:a\nEND:VTODO\nBEGIN:VTODO\nSUMMARY:b\n"
    )

    for _ in range(2):
        with patch("todoman.model.logger", spec=True) as mocked_logger:
            result = runner.invoke(cli, ["list"])
            assert " a " in result.output
            assert " b " in result.output
        assert mocked_logger.warning.call_count == 1
        assert mocked_logger.warning.call_args == mock.call(
            "Todo is in read-only mode because there are multiple todos in %s",
            path,
        )

    result = runner.invoke(cli, ["done", "1"])
    assert result.exception
    assert "Todo is in read-only mode because there are multiple todos" in result.output

    result = runner.invoke(cli, ["show", "1"])
    assert not result.exception
    result = runner.invoke(cli, ["show", "2"])
    assert not result.exception


def test_todo_new(runner, default_database):
    # This isn't a very thurough test, but at least catches obvious regressions
    # like startup crashes or typos.

    with patch("urwid.MainLoop"):
        result = runner.invoke(cli, ["new", "-l", "default"])

    # No SUMMARY error after UI runs
    assert isinstance(result.exception, SystemExit)
    assert result.exception.args == (2,)
    assert "Error: No SUMMARY specified" in result.output


def test_todo_edit(runner, default_database, todo_factory):
    # This isn't a very thurough test, but at least catches obvious regressions
    # like startup crashes or typos.
    todo_factory()

    with patch("urwid.MainLoop"):
        result = runner.invoke(cli, ["edit", "1"])

    assert not result.exception
    assert "YARR!" in result.output


@pyicu_sensitive
@freeze_time("2017, 3, 20")
def test_list_startable(tmpdir, runner, todo_factory, config):
    todo_factory(summary="started", start=datetime.datetime(2017, 3, 15))
    todo_factory(summary="nostart")
    todo_factory(summary="unstarted", start=datetime.datetime(2017, 3, 24))

    result = runner.invoke(
        cli,
        ["list", "--startable"],
        catch_exceptions=False,
    )

    assert not result.exception
    assert "started" in result.output
    assert "nostart" in result.output
    assert "unstarted" not in result.output

    result = runner.invoke(
        cli,
        ["list"],
        catch_exceptions=False,
    )

    assert not result.exception
    assert "started" in result.output
    assert "nostart" in result.output
    assert "unstarted" in result.output

    config.write("startable = True\n", "a")

    result = runner.invoke(cli, ["list"], catch_exceptions=False)

    assert not result.exception
    assert "started" in result.output
    assert "nostart" in result.output
    assert "unstarted" not in result.output


def test_bad_start_date(runner):
    result = runner.invoke(cli, ["list", "--start"])
    assert result.exception
    assert result.output.strip() == "Error: Option '--start' requires 2 arguments."

    result = runner.invoke(cli, ["list", "--start", "before"])
    assert result.exception
    assert result.output.strip() == "Error: Option '--start' requires 2 arguments."

    result = runner.invoke(cli, ["list", "--start", "before", "not_a_date"])
    assert result.exception
    assert (
        "Invalid value for '--start': Time description not recognized: not_a_date"
        in result.output
    )

    result = runner.invoke(cli, ["list", "--start", "godzilla", "2017-03-22"])
    assert result.exception
    assert "Format should be '[before|after] [DATE]'" in result.output


def test_done(runner, todo_factory, todos):
    todo = todo_factory()

    result = runner.invoke(cli, ["done", "1"])
    assert not result.exception

    todo = next(todos(status="ANY"))
    assert todo.percent_complete == 100
    assert todo.is_completed is True

    result = runner.invoke(cli, ["done", "17"])
    assert result.exception
    assert result.output.strip() == "No todo with id 17."


def test_done_recurring(runner, todo_factory, todos):
    rrule = "FREQ=DAILY;UNTIL=20990315T020000Z"
    todo = todo_factory(rrule=rrule)

    result = runner.invoke(cli, ["done", "1"])
    assert not result.exception

    todos = todos(status="ANY")
    todo = next(todos)
    assert todo.percent_complete == 100
    assert todo.is_completed is True
    assert not todo.rrule

    todo = next(todos)
    assert todo.percent_complete == 0
    assert todo.is_completed is False
    assert todo.rrule == rrule


def test_cancel(runner, todo_factory, todos):
    todo = todo_factory()

    result = runner.invoke(cli, ["cancel", "1"])
    assert not result.exception

    todo = next(todos(status="ANY"))
    assert todo.status == "CANCELLED"


def test_id_printed_for_new(runner):
    result = runner.invoke(cli, ["new", "-l", "default", "show me an id"])
    assert not result.exception
    assert result.output.strip().startswith("[ ] 1")


def test_repl(runner):
    """Test that repl registers properly."""
    if "click_repl" not in sys.modules:
        pytest.skip('Optional dependency "click_repl" is not installed')

    result = runner.invoke(cli, ["--help"])

    assert not result.exception
    assert "repl    Start an interactive shell." in result.output
    assert "shell   Start an interactive shell." in result.output


def test_no_repl(runner):
    """Test that we work fine without click_repl installed."""
    modules = sys.modules
    if "click_repl" in modules:
        pytest.skip("Test can't be run with click_repl installed")

    result = runner.invoke(cli, ["--help"])

    assert not result.exception
    assert "repl" not in result.output
    assert "shell" not in result.output
    assert "Start an interactive shell." not in result.output


def test_status_validation():
    from todoman import cli

    @given(
        statuses=st.lists(
            st.sampled_from(Todo.VALID_STATUSES + ("ANY",)),
            min_size=1,
            max_size=5,
            unique=True,
        )
    )
    def run_test(statuses):
        validated = cli.validate_status(val=",".join(statuses)).split(",")

        if "ANY" in statuses:
            assert len(validated) == 4
        else:
            assert len(validated) == len(statuses)

        for status in validated:
            assert status in Todo.VALID_STATUSES

    run_test()


def test_bad_status_validation():
    from todoman import cli

    with pytest.raises(click.BadParameter):
        cli.validate_status(val="INVALID")

    with pytest.raises(click.BadParameter):
        cli.validate_status(val="IN-PROGRESS")


def test_status_filtering(runner, todo_factory):
    todo_factory(summary="one", status="CANCELLED")
    todo_factory(summary="two")

    result = runner.invoke(cli, ["list", "--status", "cancelled"])
    assert not result.exception
    assert len(result.output.splitlines()) == 1
    assert "one " in result.output

    result = runner.invoke(cli, ["list", "--status", "NEEDS-action"])
    assert not result.exception
    assert len(result.output.splitlines()) == 1
    assert "two" in result.output


def test_invoke_command(runner, tmpdir, config):
    config.write('default_command = "flush"\n', "a")

    flush = mock.MagicMock()
    parser = mock.MagicMock()
    flush.make_parser.return_value = parser
    parser.parse_args.return_value = {}, [], []
    with patch.dict(cli.commands, values={"flush": flush}):
        result = runner.invoke(cli, catch_exceptions=False)

    assert not result.exception
    assert not result.output.strip()
    assert flush.call_count == 1


def test_invoke_invalid_command(runner, tmpdir, config):
    config.write('default_command = "DoTheRobot"\n', "a")

    result = runner.invoke(cli, catch_exceptions=False)

    assert result.exception
    assert "Error: Invalid setting for [default_command]" in result.output


def test_new_categories_single(runner):
    result = runner.invoke(cli, ["new", "-l", "default", "--category", "mine", "title"])

    assert "[mine]" in result.output


def test_new_categories_multiple(runner):
    result = runner.invoke(
        cli, ["new", "-l", "default", "-c", "first", "-c", "second", "title"]
    )

    assert "[first, second]" in result.output


def test_list_categories_single(tmpdir, runner, create):
    category = "fizzbuzz"
    create("test.ics", f"UID:{uuid4()}\nSUMMARY:harhar\nCATEGORIES:{category}\n")
    result = runner.invoke(cli, ["list", "--category", category])
    assert not result.exception
    assert category in result.output


def test_list_categories_multiple(tmpdir, runner, create):
    category = ["git", "gud"]
    create("test.ics", f"SUMMARY:harhar\nCATEGORIES:{category[0]}\n")
    create("test1.ics", f"SUMMARY:harhar1\nCATEGORIES:{category[1]}\n")
    result = runner.invoke(
        cli, ["list", "--category", category[0], "--category", category[1]]
    )
    assert not result.exception
    assert category[0] in result.output
    assert category[1] in result.output


def test_show_priority(runner, todo_factory, todos):
    todo_factory(summary="harhar\n", priority=1)

    result = runner.invoke(cli, ["show", "1"])
    assert "!!!" in result.output


def test_priority(runner):
    result = runner.invoke(
        cli, ["new", "-l", "default", "--priority", "high", "Priority Test"]
    )

    assert "!!!" in result.output


def test_porcelain_precedence(runner, tmpdir):
    """Test that --humanize flag takes precedence over `porcelain` config"""

    path = tmpdir.join("config")
    path.write("humanize = true\n", "a")

    with patch("todoman.formatters.PorcelainFormatter") as mocked_formatter:
        runner.invoke(cli, ["--porcelain", "list"])

    assert mocked_formatter.call_count == 1


def test_duplicate_list(tmpdir, runner):
    tmpdir.join("personal1").mkdir()
    with tmpdir.join("personal1").join("displayname").open("w") as f:
        f.write("personal")

    tmpdir.join("personal2").mkdir()
    with tmpdir.join("personal2").join("displayname").open("w") as f:
        f.write("personal")

    result = runner.invoke(cli, ["list"])
    assert result.exception
    assert result.exit_code == exceptions.AlreadyExistsError.EXIT_CODE
    assert (
        result.output.strip() == "More than one list has the same identity: personal."
    )


def test_edit_raw(todo_factory, runner):
    todo = todo_factory()
    assert exists(todo.path)

    with patch("click.edit", spec=True) as mocked_edit:
        result = runner.invoke(cli, ["edit", "--raw", "1"], catch_exceptions=False)

    assert mocked_edit.call_count == 1
    assert mocked_edit.call_args == mock.call(filename=todo.path)

    assert not result.exception
    assert not result.output


def test_new_description_from_stdin(runner, todos):
    result = runner.invoke(
        cli, ["new", "-l", "default", "-r", "hello"], input="world\n"
    )
    assert not result.exception
    (todo,) = todos()
    assert "world" in todo.description
    assert "hello" in todo.summary


def test_default_priority(tmpdir, runner, create, config):
    """Test setting the due date using the default_due config parameter"""
    config.write("default_priority = 3\n", "a")

    runner.invoke(cli, ["new", "-l", "default", "aaa"])
    db = Database([tmpdir.join("default")], tmpdir.join("/default_list"))
    todo = list(db.todos())[0]

    assert todo.priority == 3


def test_no_default_priority(tmpdir, runner, create):
    """Test setting the due date using the default_due config parameter"""

    runner.invoke(cli, ["new", "-l", "default", "aaa"])

    db = Database([tmpdir.join("default")], tmpdir.join("/default_list"))
    todo = list(db.todos())[0]
    assert todo.priority == 0

    todo_file = tmpdir.join("default").join(todo.filename)
    todo_ics = todo_file.read_text("utf-8")
    assert "PRIORITY" not in todo_ics


def test_invalid_default_priority(config, runner, create):
    """Test setting the due date using the default_due config parameter"""
    config.write("default_priority = 13\n", "a")

    result = runner.invoke(cli, ["new", "-l", "default", "aaa"])
    assert result.exception
    assert "Error: Invalid `default_priority` settings." in result.output


def test_default_command_args(config, runner):
    config.write(
        'default_command = "list --sort=due --due 168 ' '--priority low --no-reverse"',
        "a",
    )

    with patch("todoman.model.Database.todos", spec=True) as todos:
        result = runner.invoke(cli)

    assert not result.exception
    assert todos.call_args == call(
        sort=["due"],
        due=168,
        priority=9,
        reverse=False,
        lists=[],
        location=None,
        categories=(),
        grep=None,
        start=None,
        startable=None,
        status="NEEDS-ACTION,IN-PROCESS",
    )
