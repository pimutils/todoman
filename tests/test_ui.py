from datetime import datetime

import pytest
import pytz
from freezegun import freeze_time
from urwid import ExitMainLoop

from todoman.ui import TodoEditor, TodoFormatter

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"


def test_todo_editor_priority(default_database, todo_factory):
    todo = todo_factory(priority=1)
    lists = list(default_database.lists())
    formatter = TodoFormatter(DATE_FORMAT, TIME_FORMAT, ' ')

    editor = TodoEditor(todo, lists, formatter)
    assert editor._priority.edit_text == 'high'

    editor._priority.edit_text = ''
    with pytest.raises(ExitMainLoop):  # Look at editor._msg_text if this fails
        editor._keypress('ctrl s')

    # FileTodo exposes 0
    assert todo.priority is 0
    # The actual todo contains None
    assert todo.todo.get('priority', None) is None


def test_todo_editor_summary(default_database, todo_factory):
    todo = todo_factory()
    lists = list(default_database.lists())
    formatter = TodoFormatter(DATE_FORMAT, TIME_FORMAT, ' ')

    editor = TodoEditor(todo, lists, formatter)
    assert editor._summary.edit_text == 'YARR!'

    editor._summary.edit_text = 'Goodbye'
    with pytest.raises(ExitMainLoop):  # Look at editor._msg_text if this fails
        editor._keypress('ctrl s')

    assert todo.summary == 'Goodbye'


@freeze_time('2017-03-04 14:00:00', tz_offset=4)
def test_todo_editor_due(default_database, todo_factory):
    tz = pytz.timezone('CET')

    todo = todo_factory(due=datetime(2017, 3, 4, 14))
    lists = list(default_database.lists())
    formatter = TodoFormatter(DATE_FORMAT, TIME_FORMAT, ' ')
    formatter._localtimezone = tz

    editor = TodoEditor(todo, lists, formatter)
    assert editor._due.edit_text == '2017-03-04 14:00'

    editor._due.edit_text = '2017-03-10 12:00'
    with pytest.raises(ExitMainLoop):  # Look at editor._msg_text if this fails
        editor._keypress('ctrl s')

    assert todo.due == datetime(2017, 3, 10, 12, tzinfo=tz)
