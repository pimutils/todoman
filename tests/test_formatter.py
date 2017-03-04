from datetime import datetime, timedelta
from random import randrange

from todoman import ui

DATE_FORMAT = "%d-%m-%y"
TIME_FORMAT = "%H:%M"


def test_human_dates():
    formatter = ui.TodoFormatter(DATE_FORMAT, TIME_FORMAT, ' ')
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    tomorrow_12am = datetime(tomorrow.year, tomorrow.month, tomorrow.day,
                             12, 0)
    today_12am = datetime(today.year, today.month, today.day,
                          12, 0)
    any_day = today + timedelta(days=randrange(2, 8))

    assert formatter.format_datetime("") == ''
    assert formatter._format_date(today.date()) == "Today"
    assert formatter._format_date(tomorrow.date()) == "Tomorrow"
    assert formatter.format_datetime(any_day) == \
        any_day.strftime(DATE_FORMAT + ' ' + TIME_FORMAT)
    assert formatter.format_datetime(tomorrow_12am) == "Tomorrow 12:00"
    assert formatter.parse_datetime('12:00').replace(tzinfo=None) == today_12am


def test_format_priority():
    formatter = ui.TodoFormatter('', '', '')

    assert formatter.format_priority(None) == ''
    assert formatter.format_priority(0) == ''
    assert formatter.format_priority(5) == 'medium'
    for i in range(1, 5):
        assert formatter.format_priority(i) == 'high'
    for i in range(6, 10):
        assert formatter.format_priority(i) == 'low'


def test_format_priority_compact():
    formatter = ui.TodoFormatter('', '', '')

    assert formatter.format_priority_compact(None) == ''
    assert formatter.format_priority_compact(0) == ''
    assert formatter.format_priority_compact(5) == '!!'
    for i in range(1, 5):
        assert formatter.format_priority_compact(i) == '!!!'
    for i in range(6, 10):
        assert formatter.format_priority_compact(i) == '!'
