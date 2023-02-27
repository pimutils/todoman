import json
from datetime import datetime
from uuid import uuid4

import pytz

from todoman.cli import cli
from todoman.formatters import PorcelainFormatter


def test_list_all(tmpdir, runner, create):
    create(
        "test.ics",
        "SUMMARY:Do stuff\n"
        "STATUS:COMPLETED\n"
        "COMPLETED:20181225T191234Z\n"
        "DUE;VALUE=DATE-TIME;TZID=CET:20160102T000000\n"
        "DTSTART:20160101T000000Z\n"
        "PERCENT-COMPLETE:26\n"
        "LOCATION:Wherever\n",
    )
    result = runner.invoke(cli, ["--porcelain", "list", "--status", "ANY"])

    expected = [
        {
            "categories": [],
            "completed": True,
            "completed_at": 1545765154,
            "description": "",
            "due": 1451689200,
            "id": 1,
            "list": "default",
            "location": "Wherever",
            "percent": 26,
            "priority": 0,
            "start": 1451606400,
            "summary": "Do stuff",
        }
    ]

    assert not result.exception
    assert result.output.strip() == json.dumps(expected, indent=4, sort_keys=True)


def test_list_start_date(tmpdir, runner, create):
    create(
        "test.ics",
        "SUMMARY:Do stuff\n"
        "STATUS:COMPLETED\n"
        "DTSTART;VALUE=DATE:20160102\n"
        "PERCENT-COMPLETE:26\n"
        "LOCATION:Wherever\n",
    )
    result = runner.invoke(cli, ["--porcelain", "list", "--status", "ANY"])

    expected = [
        {
            "categories": [],
            "completed": True,
            "completed_at": None,
            "description": "",
            "due": None,
            "id": 1,
            "list": "default",
            "location": "Wherever",
            "percent": 26,
            "priority": 0,
            "start": 1451692800,
            "summary": "Do stuff",
        }
    ]

    assert not result.exception
    assert result.output.strip() == json.dumps(expected, indent=4, sort_keys=True)


def test_list_due_date(tmpdir, runner, create):
    create(
        "test.ics",
        "SUMMARY:Do stuff\n"
        "STATUS:COMPLETED\n"
        "DUE;VALUE=DATE:20160102\n"
        "PERCENT-COMPLETE:26\n"
        "LOCATION:Wherever\n",
    )
    result = runner.invoke(cli, ["--porcelain", "list", "--status", "ANY"])

    expected = [
        {
            "categories": [],
            "completed": True,
            "completed_at": None,
            "description": "",
            "due": 1451692800,
            "id": 1,
            "list": "default",
            "location": "Wherever",
            "percent": 26,
            "priority": 0,
            "start": None,
            "summary": "Do stuff",
        }
    ]

    assert not result.exception
    assert result.output.strip() == json.dumps(expected, indent=4, sort_keys=True)


def test_list_nodue(tmpdir, runner, create):
    create(
        "test.ics",
        f"UID:{uuid4()}\nSUMMARY:Do stuff\nPERCENT-COMPLETE:12\nPRIORITY:4\n",
    )
    result = runner.invoke(cli, ["--porcelain", "list"])

    expected = [
        {
            "categories": [],
            "completed": False,
            "completed_at": None,
            "description": "",
            "due": None,
            "id": 1,
            "list": "default",
            "location": "",
            "percent": 12,
            "priority": 4,
            "start": None,
            "summary": "Do stuff",
        }
    ]

    assert not result.exception
    assert result.output.strip() == json.dumps(expected, indent=4, sort_keys=True)


def test_list_priority(tmpdir, runner, create):
    result = runner.invoke(cli, ["--porcelain", "list"], catch_exceptions=False)
    assert not result.exception
    assert result.output.strip() == "[]"
    create("one.ics", f"UID:{uuid4()}\nSUMMARY:haha\nPRIORITY:4\n")
    create("two.ics", f"UID:{uuid4()}\nSUMMARY:hoho\nPRIORITY:9\n")
    create("three.ics", f"UID:{uuid4()}\nSUMMARY:hehe\nPRIORITY:5\n")
    create("four.ics", f"UID:{uuid4()}\nSUMMARY:huhu\n")

    result_high = runner.invoke(cli, ["--porcelain", "list", "--priority=4"])
    assert not result_high.exception
    assert "haha" in result_high.output
    assert "hoho" not in result_high.output
    assert "huhu" not in result_high.output
    assert "hehe" not in result_high.output

    result_medium = runner.invoke(cli, ["--porcelain", "list", "--priority=5"])
    assert not result_medium.exception
    assert "haha" in result_medium.output
    assert "hehe" in result_medium.output
    assert "hoho" not in result_medium.output
    assert "huhu" not in result_medium.output

    result_low = runner.invoke(cli, ["--porcelain", "list", "--priority=9"])
    assert not result_low.exception
    assert "haha" in result_low.output
    assert "hehe" in result_low.output
    assert "hoho" in result_low.output
    assert "huhu" not in result_low.output

    result_none = runner.invoke(cli, ["--porcelain", "list", "--priority=0"])
    assert not result_none.exception
    assert "haha" in result_none.output
    assert "hehe" in result_none.output
    assert "hoho" in result_none.output
    assert "huhu" in result_none.output

    result_error = runner.invoke(cli, ["--porcelain", "list", "--priority=18"])
    assert result_error.exception


def test_show(tmpdir, runner, create):
    create(
        "test.ics",
        f"UID:{uuid4()}\nSUMMARY:harhar\n"
        "DESCRIPTION:Lots of text. Yum!\nPRIORITY:5\n",
    )
    result = runner.invoke(cli, ["--porcelain", "show", "1"])

    expected = {
        "categories": [],
        "completed": False,
        "completed_at": None,
        "description": "Lots of text. Yum!",
        "due": None,
        "id": 1,
        "list": "default",
        "location": "",
        "percent": 0,
        "priority": 5,
        "start": None,
        "summary": "harhar",
    }

    assert not result.exception
    assert result.output.strip() == json.dumps(expected, indent=4, sort_keys=True)


def test_simple_action(todo_factory):
    formatter = PorcelainFormatter()
    todo = todo_factory(id=7, location="Downtown")

    expected = {
        "categories": [],
        "completed": False,
        "completed_at": None,
        "description": "",
        "due": None,
        "id": 7,
        "list": "default",
        "location": "Downtown",
        "percent": 0,
        "priority": 0,
        "start": None,
        "summary": "YARR!",
    }

    assert formatter.simple_action("Delete", todo) == json.dumps(
        expected, indent=4, sort_keys=True
    )


def test_format_datetime():
    formatter = PorcelainFormatter()

    dt = datetime(2017, 3, 8, 0, 0, 17, 457955, tzinfo=pytz.UTC)
    t = 1488931217

    assert formatter.format_datetime(dt) == t


def test_parse_datetime():
    formatter = PorcelainFormatter()

    expected = datetime(2017, 3, 6, 23, 22, 21, 610429, tzinfo=pytz.UTC)
    assert formatter.parse_datetime(1488842541.610429) == expected

    assert formatter.parse_datetime(None) is None
    assert formatter.parse_datetime("") is None


def test_formatting_parsing_consitency():
    tz = pytz.timezone("CET")
    dt = datetime(2017, 3, 8, 21, 6, 19).replace(tzinfo=tz)

    formatter = PorcelainFormatter(tz_override=tz)
    assert formatter.parse_datetime(formatter.format_datetime(dt)) == dt
