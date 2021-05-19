from unittest import mock

from todoman.widgets import ExtendedEdit
from todoman.widgets import PrioritySelector

# We ignore `size` when testing keypresses, because it's not used anywhere.
# Just pass any number when writing tests, unless we start using the value.

BASE_STRING = "The lazy fox bla bla\n@ät"


def test_extended_edit_delete_word():
    extended_edit = ExtendedEdit(None)

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 9
    extended_edit.keypress(10, "ctrl w")
    assert extended_edit.edit_pos == 4
    assert extended_edit.get_edit_text() == "The fox bla bla\n@ät"

    extended_edit.set_edit_text("The-lazy-fox-bla-bla\n@ät")
    extended_edit.edit_pos = 8
    extended_edit.keypress(10, "ctrl w")
    assert extended_edit.edit_pos == 4
    assert extended_edit.get_edit_text() == "The--fox-bla-bla\n@ät"

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 6
    extended_edit.keypress(10, "ctrl w")
    assert extended_edit.edit_pos == 4
    assert extended_edit.get_edit_text() == "The zy fox bla bla\n@ät"

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 0
    extended_edit.keypress(10, "ctrl w")
    assert extended_edit.edit_pos == 0
    assert extended_edit.get_edit_text() == BASE_STRING


def test_extended_edit_delete_sol():
    extended_edit = ExtendedEdit(None)

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 9
    extended_edit.keypress(10, "ctrl u")
    assert extended_edit.edit_pos == 0
    assert extended_edit.get_edit_text() == "fox bla bla\n@ät"

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 0
    extended_edit.keypress(10, "ctrl u")
    assert extended_edit.edit_pos == 0
    assert extended_edit.get_edit_text() == BASE_STRING


def test_extended_edit_delete_eol():
    extended_edit = ExtendedEdit(None)

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 9
    extended_edit.keypress(10, "ctrl k")
    assert extended_edit.edit_pos == 9
    assert extended_edit.get_edit_text() == "The lazy \n@ät"

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 20
    extended_edit.keypress(10, "ctrl k")
    assert extended_edit.edit_pos == 20
    assert extended_edit.get_edit_text() == BASE_STRING

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 24
    extended_edit.keypress(10, "ctrl k")
    assert extended_edit.edit_pos == 24
    assert extended_edit.get_edit_text() == BASE_STRING


def test_extended_edit_goto_sol():
    extended_edit = ExtendedEdit(None)

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 9
    extended_edit.keypress(10, "ctrl a")
    assert extended_edit.edit_pos == 0
    assert extended_edit.get_edit_text() == BASE_STRING

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 23
    extended_edit.keypress(10, "ctrl a")
    assert extended_edit.edit_pos == 21
    assert extended_edit.get_edit_text() == BASE_STRING


def test_extended_edit_goto_eol():
    extended_edit = ExtendedEdit(None)

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 9
    extended_edit.keypress(10, "ctrl e")
    assert extended_edit.edit_pos == 20
    assert extended_edit.get_edit_text() == BASE_STRING

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 22
    extended_edit.keypress(10, "ctrl e")
    assert extended_edit.edit_pos == 24
    assert extended_edit.get_edit_text() == BASE_STRING


def test_extended_edit_delete_next_char():
    extended_edit = ExtendedEdit(None)

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 9
    extended_edit.keypress(10, "ctrl d")
    assert extended_edit.edit_pos == 9
    assert extended_edit.get_edit_text() == "The lazy ox bla bla\n@ät"

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 0
    extended_edit.keypress(10, "ctrl d")
    assert extended_edit.edit_pos == 0
    assert extended_edit.get_edit_text() == "he lazy fox bla bla\n@ät"

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 24
    extended_edit.keypress(10, "ctrl d")
    assert extended_edit.edit_pos == 24
    assert extended_edit.get_edit_text() == "The lazy fox bla bla\n@ät"

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 24
    extended_edit.keypress(10, "ctrl d")
    assert extended_edit.edit_pos == 24
    assert extended_edit.get_edit_text() == "The lazy fox bla bla\n@ät"


def test_extended_edit_input():
    """
    Very basic test to make sure we don't break basic editing

    We don't need to do more testing because that's done upstream. We basically
    want to test that we properly forward unhandled keypresses.
    """
    extended_edit = ExtendedEdit(mock.MagicMock())
    extended_edit.keypress((10,), "h")
    extended_edit.keypress((10,), "i")

    assert extended_edit.get_edit_text() == "hi"


def test_extended_edit_editor():
    extended_edit = ExtendedEdit(mock.MagicMock())
    extended_edit.set_edit_text(BASE_STRING)

    with mock.patch("click.edit", return_value="Sheep!") as edit:
        extended_edit.keypress(10, "ctrl o")

    assert edit.call_count == 1
    assert edit.call_args == mock.call(BASE_STRING)
    assert extended_edit.get_edit_text() == "Sheep!"


def test_priority_selector(default_formatter):
    selector = PrioritySelector(None, 5, default_formatter.format_priority)

    assert selector.label == "medium"
    assert selector.priority == 5

    selector.keypress(10, "right")
    assert selector.label == "high"
    assert selector.priority == 1

    selector.keypress(10, "left")
    selector.keypress(10, "left")
    assert selector.label == "low"
    assert selector.priority == 9

    selector.keypress(10, "right")
    assert selector.label == "medium"
    assert selector.priority == 5

    # Spin the whoel way around:
    for _ in PrioritySelector.RANGES:
        selector.keypress(10, "right")

    assert selector.label == "medium"
    assert selector.priority == 5

    # Now the other way
    for _ in PrioritySelector.RANGES:
        selector.keypress(10, "left")

    assert selector.label == "medium"
    assert selector.priority == 5

    # Should do nothing:
    selector.keypress(10, "d")
    selector.keypress(10, "9")
    assert selector.label == "medium"
    assert selector.priority == 5
