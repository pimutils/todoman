import pytest
from urwid import ExitMainLoop

from todoman.ui import TodoEditor, TodoFormatter

DATE_FORMAT = "%d-%m-%y"
TIME_FORMAT = "%H:%M"


def test_todo_editor_priority(default_database, todo_factory):
    todo = todo_factory(priority=1)
    lists = list(default_database.lists())
    formatter = TodoFormatter(DATE_FORMAT, TIME_FORMAT, '')

    editor = TodoEditor(todo, lists, formatter)
    editor._priority.edit_text = ''

    with pytest.raises(ExitMainLoop):  # Look at editor._msg_text if this fails
        editor._keypress('ctrl s')

    # FileTodo exposes 0
    assert todo.priority is 0
    # The actual todo contains None
    assert todo.todo.get('priority', None) is None
