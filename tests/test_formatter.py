from datetime import date, datetime, time, timedelta

import pytest
import pytz
from freezegun import freeze_time

from todoman.cli import cli


@pytest.mark.parametrize('interval', [
    (65, 'in a minute'),
    (-10800, '3 hours ago'),
])
@pytest.mark.parametrize('tz', ['CET', 'HST'])
@freeze_time('2017-03-25')
def test_humanized_date(runner, create, interval, now_for_tz, tz):
    seconds, expected = interval
    due = now_for_tz(tz) + timedelta(seconds=seconds)
    create(
        'test.ics',
        'SUMMARY:Hi human!\n'
        'DUE;VALUE=DATE-TIME;TZID={}:{}\n'
        .format(tz, due.strftime('%Y%m%dT%H%M%S'))
    )

    result = runner.invoke(cli, ['--humanize', 'list', '--status', 'ANY'])
    assert not result.exception
    assert expected in result.output


def test_format_priority(default_formatter):
    assert default_formatter.format_priority(None) == 'none'
    assert default_formatter.format_priority(0) == 'none'
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

    # TODO:use formatter instead of runner?
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


def test_parse_time(default_formatter):
    tz = pytz.timezone('CET')
    parsed = default_formatter.parse_datetime('12:00')
    expected = datetime.combine(
        date.today(),
        time(hour=12, minute=0),
    ).replace(tzinfo=tz)
    assert parsed == expected


def test_parse_datetime(default_formatter):
    tz = pytz.timezone('CET')

    parsed = default_formatter.parse_datetime('2017-03-05')
    assert parsed == datetime(2017, 3, 5).replace(tzinfo=tz)

    parsed = default_formatter.parse_datetime('2017-03-05 12:00')
    assert parsed == datetime(2017, 3, 5, 12).replace(tzinfo=tz)

    # Notes. will round to the NEXT matching date, so we need to freeze time
    # for this one:
    with freeze_time('2017-03-04'):
        parsed = default_formatter.parse_datetime(
            'Mon Mar  6 22:50:52 -03 2017'
        )
    assert parsed == datetime(2017, 3, 6, 20, 17).replace(tzinfo=tz)

    assert default_formatter.parse_datetime('') is None

    assert default_formatter.parse_datetime(None) is None


def test_humanized_parse_datetime(humanized_formatter):
    tz = pytz.timezone('CET')

    humanized_formatter.now = datetime(2017, 3, 6, 22, 17).replace(tzinfo=tz)
    dt = datetime(2017, 3, 6, 20, 17).replace(tzinfo=tz)

    assert humanized_formatter.format_datetime(dt) == '2 hours ago'
    assert humanized_formatter.format_datetime(None) == ''


def test_simple_action(default_formatter, todo_factory):
    todo = todo_factory()
    assert default_formatter.simple_action('Delete', todo) == \
        'Delete "YARR!"'


def test_formatting_parsing_consitency(default_formatter):
    tz = pytz.timezone('CET')
    dt = datetime(2017, 3, 8, 21, 6).replace(tzinfo=tz)

    formatted = default_formatter.format_datetime(dt)
    assert default_formatter.parse_datetime(formatted) == dt
