from todoman.model import FileTodo
from todoman.ui import PorcelainFormatter, TodoEditor


def test_todo_editor(default_database):
    """
    Tests TodoEditor

    While this is a pretty lame test, it's a lot better than nothing until we
    have a proper testing framework for the interactive parts.

    It basically makes sure that we don't refer to any obsolete methods, etc.
    """

    lists = list(default_database.lists())

    todo = FileTodo(new=True)
    todo.list = lists[0]
    todo.summary = 'YARR!'
    todo.save()

    porcelain_formatter = PorcelainFormatter()

    editor = TodoEditor(todo, lists, porcelain_formatter)

    editor._keypress('ctrl s')
