from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta

import pytest
import pytz
from freezegun import freeze_time

from tests.helpers import pyicu_sensitive
from todoman.cli import cli
from todoman.formatters import rgb_to_ansi


@pyicu_sensitive
@pytest.mark.parametrize("interval", [(65, "in a minute"), (-10800, "3 hours ago")])
@pytest.mark.parametrize("tz", ["CET", "HST"])
@freeze_time("2017-03-25")
def test_humanized_datetime(runner, create, interval, now_for_tz, tz):
    seconds, expected = interval
    due = now_for_tz(tz) + timedelta(seconds=seconds)
    create(
        "test.ics",
        "SUMMARY:Hi human!\nDUE;VALUE=DATE-TIME;TZID={}:{}\n".format(
            tz, due.strftime("%Y%m%dT%H%M%S")
        ),
    )

    result = runner.invoke(cli, ["--humanize", "list", "--status", "ANY"])
    assert not result.exception
    assert expected in result.output


@pyicu_sensitive
@pytest.mark.parametrize("interval", [(65, "today"), (-10800, "today")])
@pytest.mark.parametrize("tz", ["CET", "HST"])
@freeze_time("2017-03-25 18:00:00")
def test_humanized_date(runner, create, interval, now_for_tz, tz):
    seconds, expected = interval
    due = now_for_tz(tz) + timedelta(seconds=seconds)
    create(
        "test.ics",
        "SUMMARY:Hi human!\nDUE;VALUE=DATE;TZID={}:{}\n".format(
            tz, due.strftime("%Y%m%d")
        ),
    )

    result = runner.invoke(cli, ["--humanize", "list", "--status", "ANY"])
    assert not result.exception
    assert expected in result.output


def test_format_priority(default_formatter):
    assert default_formatter.format_priority(None) == "none"
    assert default_formatter.format_priority(0) == "none"
    assert default_formatter.format_priority(5) == "medium"
    for i in range(1, 5):
        assert default_formatter.format_priority(i) == "high"
    for i in range(6, 10):
        assert default_formatter.format_priority(i) == "low"

    with pytest.raises(ValueError, match="priority is an invalid value"):
        assert default_formatter.format_priority(12)


def test_format_priority_compact(default_formatter):
    assert default_formatter.format_priority_compact(None) == ""
    assert default_formatter.format_priority_compact(0) == ""
    assert default_formatter.format_priority_compact(5) == "!!"
    for i in range(1, 5):
        assert default_formatter.format_priority_compact(i) == "!!!"
    for i in range(6, 10):
        assert default_formatter.format_priority_compact(i) == "!"

    with pytest.raises(ValueError, match="priority is an invalid value"):
        assert default_formatter.format_priority_compact(12)


def test_format_date(default_formatter):
    assert default_formatter.format_datetime(date(2017, 3, 4)) == "2017-03-04"


def test_format_datetime(default_formatter):
    assert (
        default_formatter.format_datetime(datetime(2017, 3, 4, 17, 00))
        == "2017-03-04 17:00"
    )


def test_detailed_format(runner, todo_factory):
    todo_factory(
        description=(
            "Test detailed formatting\nThis includes multiline descriptions\nBlah!"
        ),
        location="Over the hills, and far away",
    )

    # TODO:use formatter instead of runner?
    result = runner.invoke(cli, ["show", "1"])
    expected = [
        "[ ] 1  (no due date) YARR! @default",
        "",
        "Description:",
        "Test detailed formatting",
        "This includes multiline descriptions",
        "Blah!",
        "",
        "Location: Over the hills, and far away",
    ]

    assert not result.exception
    assert result.output.strip().splitlines() == expected


def test_parse_time(default_formatter):
    tz = pytz.timezone("CET")
    parsed = default_formatter.parse_datetime("12:00")
    expected = datetime.combine(
        date.today(),
        time(hour=12, minute=0),
    ).replace(tzinfo=tz)
    assert parsed == expected


def test_parse_datetime(default_formatter):
    tz = pytz.timezone("CET")

    parsed = default_formatter.parse_datetime("2017-03-05")
    assert parsed == date(2017, 3, 5)

    parsed = default_formatter.parse_datetime("2017-03-05 12:00")
    assert parsed == datetime(2017, 3, 5, 12).replace(tzinfo=tz)

    # Notes. will round to the NEXT matching date, so we need to freeze time
    # for this one:
    with freeze_time("2017-03-04"):
        parsed = default_formatter.parse_datetime("Mon Mar  6 22:50:52 -03 2017")
    assert parsed == datetime(2017, 3, 6, 20, 17).replace(tzinfo=tz)

    assert default_formatter.parse_datetime("") is None

    assert default_formatter.parse_datetime(None) is None


def test_humanized_parse_datetime(humanized_formatter):
    tz = pytz.timezone("CET")

    humanized_formatter.now = datetime(2017, 3, 6, 22, 17).replace(tzinfo=tz)
    dt = datetime(2017, 3, 6, 20, 17).replace(tzinfo=tz)

    assert humanized_formatter.format_datetime(dt) == "2 hours ago"
    assert humanized_formatter.format_datetime(None) == ""


def test_simple_action(default_formatter, todo_factory):
    todo = todo_factory()
    assert default_formatter.simple_action("Delete", todo) == 'Delete "YARR!"'


def test_formatting_parsing_consitency(default_formatter):
    tz = pytz.timezone("CET")
    dt = datetime(2017, 3, 8, 21, 6).replace(tzinfo=tz)

    formatted = default_formatter.format_datetime(dt)
    assert default_formatter.parse_datetime(formatted) == dt


def test_rgb_to_ansi():
    assert rgb_to_ansi(None) is None
    assert rgb_to_ansi("#8ab6d") is None
    assert rgb_to_ansi("#8ab6d2f") == "\x1b[38;2;138;182;210m"
    assert rgb_to_ansi("red") is None
    assert rgb_to_ansi("#8ab6d2") == "\x1b[38;2;138;182;210m"


def test_format_multiple_with_list(default_formatter, todo_factory):
    todo = todo_factory()
    assert todo.list
    assert (
        default_formatter.compact_multiple([todo])
        == "[ ] 1 \x1b[35m\x1b[0m \x1b[37m(no due date)\x1b[0m YARR! @default\x1b[0m"
    )


def test_format_multiple_without_list(default_formatter, todo_factory):
    todo = todo_factory()
    todo.list = None
    assert not todo.list
    with pytest.raises(ValueError, match="Cannot format todo without a list"):
        default_formatter.compact_multiple([todo])
