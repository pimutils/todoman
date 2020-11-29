from datetime import datetime
from unittest import mock

import pytest
import pytz
from freezegun import freeze_time
from urwid import ExitMainLoop

from todoman.interactive import TodoEditor


def test_todo_editor_priority(default_database, todo_factory, default_formatter):
    todo = todo_factory(priority=1)
    lists = list(default_database.lists())

    editor = TodoEditor(todo, lists, default_formatter)
    assert editor._priority.label == "high"

    editor._priority.keypress(10, "right")
    with pytest.raises(ExitMainLoop):  # Look at editor._msg_text if this fails
        editor._keypress("ctrl s")

    assert todo.priority == 0


def test_todo_editor_list(default_database, todo_factory, default_formatter, tmpdir):
    tmpdir.mkdir("another_list")

    default_database.paths = [
        str(tmpdir.join("default")),
        str(tmpdir.join("another_list")),
    ]
    default_database.update_cache()

    todo = todo_factory()
    lists = list(default_database.lists())

    editor = TodoEditor(todo, lists, default_formatter)
    default_list = next(filter(lambda x: x.label == "default", editor.list_selector))
    another_list = next(
        filter(lambda x: x.label == "another_list", editor.list_selector)
    )

    assert editor.current_list == todo.list
    assert default_list.label == todo.list.name

    another_list.set_state(True)
    editor._save_inner()

    assert editor.current_list == todo.list
    assert another_list.label == todo.list.name


def test_todo_editor_summary(default_database, todo_factory, default_formatter):
    todo = todo_factory()
    lists = list(default_database.lists())

    editor = TodoEditor(todo, lists, default_formatter)
    assert editor._summary.edit_text == "YARR!"

    editor._summary.edit_text = "Goodbye"
    with pytest.raises(ExitMainLoop):  # Look at editor._msg_text if this fails
        editor._keypress("ctrl s")

    assert todo.summary == "Goodbye"


@freeze_time("2017-03-04 14:00:00", tz_offset=4)
def test_todo_editor_due(default_database, todo_factory, default_formatter):
    tz = pytz.timezone("CET")

    todo = todo_factory(due=datetime(2017, 3, 4, 14))
    lists = list(default_database.lists())
    default_formatter.tz = tz

    editor = TodoEditor(todo, lists, default_formatter)
    assert editor._due.edit_text == "2017-03-04 14:00"

    editor._due.edit_text = "2017-03-10 12:00"
    with pytest.raises(ExitMainLoop):  # Look at editor._msg_text if this fails
        editor._keypress("ctrl s")

    assert todo.due == datetime(2017, 3, 10, 12, tzinfo=tz)


def test_toggle_help(default_database, default_formatter, todo_factory):
    todo = todo_factory()
    lists = list(default_database.lists())

    editor = TodoEditor(todo, lists, default_formatter)
    editor._loop = mock.MagicMock()
    assert editor._help_text not in editor.left_column.body.contents

    editor._keypress("f1")
    # Help text is made visible
    assert editor._help_text in editor.left_column.body.contents

    # Called event_loop.draw_screen
    assert editor._loop.draw_screen.call_count == 1
    assert editor._loop.draw_screen.call_args == mock.call()

    editor._keypress("f1")
    # Help text is made visible
    assert editor._help_text not in editor.left_column.body.contents

    # Called event_loop.draw_screen
    assert editor._loop.draw_screen.call_count == 2
    assert editor._loop.draw_screen.call_args == mock.call()


def test_show_save_errors(default_database, default_formatter, todo_factory):
    todo = todo_factory()
    lists = list(default_database.lists())

    editor = TodoEditor(todo, lists, default_formatter)
    # editor._loop = mock.MagicMock()

    editor._due.set_edit_text("not a date")
    editor._keypress("ctrl s")

    assert (
        editor.left_column.body.contents[2].get_text()[0]
        == "Time description not recognized: not a date"
    )


@pytest.mark.parametrize("completed", [True, False])
@pytest.mark.parametrize("check", [True, False])
def test_save_completed(check, completed, default_formatter, todo_factory):
    todo = todo_factory()
    if completed:
        todo.complete()
    editor = TodoEditor(todo, [todo.list], default_formatter)

    editor._completed.state = check
    with pytest.raises(ExitMainLoop):
        editor._keypress("ctrl s")
    assert todo.is_completed is check


def test_ctrl_c_clears(default_formatter, todo_factory):
    todo = todo_factory()
    editor = TodoEditor(todo, [todo.list], default_formatter)

    # Simulate that ctrl+c gets pressed, since we can't *really* do that
    # trivially inside unit tests.
    with mock.patch(
        "urwid.main_loop.MainLoop.run", side_effect=KeyboardInterrupt
    ), mock.patch(
        "urwid.main_loop.MainLoop.stop",
    ) as mocked_stop:
        editor.edit()

    assert mocked_stop.call_count == 1
