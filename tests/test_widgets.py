from todoman.widgets import ExtendedEdit

# We ignore `size` when testing keypresses, because it's not used anywhere.
# Just pass any number when writing tests, unless we start using the value.

BASE_STRING = 'The lazy fox bla bla\n@ät'


def test_extended_edit_delete_word():
    extended_edit = ExtendedEdit(None)

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 9
    extended_edit.keypress(10, 'ctrl w')
    assert extended_edit.edit_pos == 4
    assert extended_edit.get_edit_text() == 'The fox bla bla\n@ät'

    extended_edit.set_edit_text('The-lazy-fox-bla-bla\n@ät')
    extended_edit.edit_pos = 8
    extended_edit.keypress(10, 'ctrl w')
    assert extended_edit.edit_pos == 4
    assert extended_edit.get_edit_text() == 'The--fox-bla-bla\n@ät'

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 6
    extended_edit.keypress(10, 'ctrl w')
    assert extended_edit.edit_pos == 4
    assert extended_edit.get_edit_text() == 'The zy fox bla bla\n@ät'

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 0
    extended_edit.keypress(10, 'ctrl w')
    assert extended_edit.edit_pos == 0
    assert extended_edit.get_edit_text() == BASE_STRING


def test_extended_edit_delete_sol():
    extended_edit = ExtendedEdit(None)

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 9
    extended_edit.keypress(10, 'ctrl u')
    assert extended_edit.edit_pos == 0
    assert extended_edit.get_edit_text() == 'fox bla bla\n@ät'

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 0
    extended_edit.keypress(10, 'ctrl u')
    assert extended_edit.edit_pos == 0
    assert extended_edit.get_edit_text() == BASE_STRING


def test_extended_edit_delete_eol():
    extended_edit = ExtendedEdit(None)

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 9
    extended_edit.keypress(10, 'ctrl k')
    assert extended_edit.edit_pos == 9
    assert extended_edit.get_edit_text() == 'The lazy \n@ät'

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 20
    extended_edit.keypress(10, 'ctrl k')
    assert extended_edit.edit_pos == 20
    assert extended_edit.get_edit_text() == BASE_STRING

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 24
    extended_edit.keypress(10, 'ctrl k')
    assert extended_edit.edit_pos == 24
    assert extended_edit.get_edit_text() == BASE_STRING


def test_extended_edit_goto_sol():
    extended_edit = ExtendedEdit(None)

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 9
    extended_edit.keypress(10, 'ctrl a')
    assert extended_edit.edit_pos == 0
    assert extended_edit.get_edit_text() == BASE_STRING

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 23
    extended_edit.keypress(10, 'ctrl a')
    assert extended_edit.edit_pos == 21
    assert extended_edit.get_edit_text() == BASE_STRING


def test_extended_edit_goto_eol():
    extended_edit = ExtendedEdit(None)

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 9
    extended_edit.keypress(10, 'ctrl e')
    assert extended_edit.edit_pos == 20
    assert extended_edit.get_edit_text() == BASE_STRING

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 22
    extended_edit.keypress(10, 'ctrl e')
    assert extended_edit.edit_pos == 24
    assert extended_edit.get_edit_text() == BASE_STRING


def test_extended_edit_delete_next_char():
    extended_edit = ExtendedEdit(None)

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 9
    extended_edit.keypress(10, 'ctrl d')
    assert extended_edit.edit_pos == 9
    assert extended_edit.get_edit_text() == 'The lazy ox bla bla\n@ät'

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 0
    extended_edit.keypress(10, 'ctrl d')
    assert extended_edit.edit_pos == 0
    assert extended_edit.get_edit_text() == 'he lazy fox bla bla\n@ät'

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 24
    extended_edit.keypress(10, 'ctrl d')
    assert extended_edit.edit_pos == 24
    assert extended_edit.get_edit_text() == 'The lazy fox bla bla\n@ät'

    extended_edit.set_edit_text(BASE_STRING)
    extended_edit.edit_pos = 24
    extended_edit.keypress(10, 'ctrl d')
    assert extended_edit.edit_pos == 24
    assert extended_edit.get_edit_text() == 'The lazy fox bla bla\n@ät'

# TODO: plain ol' keypresses
# TODO: can we test ctrl o (maybe with some unittest.mock?)
