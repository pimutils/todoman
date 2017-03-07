from datetime import date, datetime, timedelta

import pytest

from todoman.cli import cli


@pytest.mark.parametrize('interval', [
    (65, 'in a minute'),
    (-10800, '3 hours ago'),
])
@pytest.mark.parametrize('tz', ['CET', 'HST'])
def test_humanized_date(runner, create, interval, now_for_tz, tz):
    seconds, expected = interval
    due = now_for_tz(tz) + timedelta(seconds=seconds)
    create(
        'test.ics',
        'SUMMARY:Hi human!\n'
        'DUE;VALUE=DATE-TIME;TZID={}:{}\n'
        .format(tz, due.strftime('%Y%m%dT%H%M%S'))
    )

    result = runner.invoke(cli, ['--humanize', 'list', '--all'])
    assert not result.exception
    assert expected in result.output


def test_format_priority(default_formatter):
    assert default_formatter.format_priority(None) == ''
    assert default_formatter.format_priority(0) == ''
    assert default_formatter.format_priority(5) == 'medium'
    for i in range(1, 5):
        assert default_formatter.format_priority(i) == 'high'
    for i in range(6, 10):
        assert default_formatter.format_priority(i) == 'low'


def test_format_priority_compact(default_formatter):
    assert default_formatter.format_priority_compact(None) == ''
    assert default_formatter.format_priority_compact(0) == ''
    assert default_formatter.format_priority_compact(5) == '!!'
    for i in range(1, 5):
        assert default_formatter.format_priority_compact(i) == '!!!'
    for i in range(6, 10):
        assert default_formatter.format_priority_compact(i) == '!'


def test_format_date(default_formatter):
    assert default_formatter.format_datetime(date(2017, 3, 4)) == '2017-03-04'


def test_format_datetime(default_formatter):
    assert default_formatter.format_datetime(datetime(2017, 3, 4, 17, 00)) == \
        '2017-03-04 17:00'


def test_detailed_format(runner, todo_factory):
    todo_factory(
        description='Test detailed formatting\n'
        'This includes multiline descriptions\n'
        'Blah!',
        location='Over the hills, and far away',
    )

    result = runner.invoke(cli, ['show', '1'])
    expected = (
        '1  [ ]      YARR! @default\n\n'
        'Description  Test detailed formatting\n'
        '             This includes multiline descriptions\n'
        '             Blah!\n'
        'Location     Over the hills, and far away'
    )
    assert not result.exception
    assert result.output.strip() == expected
