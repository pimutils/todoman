from __future__ import annotations

from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import tzinfo
from typing import Callable
from unittest.mock import patch
from uuid import uuid4

import py
import pytest
import pytz
from click.testing import CliRunner
from dateutil.tz import tzlocal
from dateutil.tz.tz import tzoffset
from freezegun import freeze_time

from todoman.exceptions import AlreadyExistsError
from todoman.model import Database
from todoman.model import Todo
from todoman.model import TodoList


def test_querying(create: Callable, tmpdir: py.path.local) -> None:
    for list in "abc":
        for i, location in enumerate("abc"):
            create(
                f"test{i}.ics",
                f"UID:{uuid4()}\nSUMMARY:test_querying\r\nLOCATION:{location}\r\n",
                list_name=list,
            )

    db = Database(
        [str(tmpdir.ensure_dir(list_)) for list_ in "abc"], str(tmpdir.join("cache"))
    )

    assert len(set(db.todos())) == 9
    assert len(set(db.todos(lists="ab"))) == 6
    assert len(set(db.todos(lists="ab", location="a"))) == 2


def test_retain_tz(tmpdir: py.path.local, create: Callable, todos: Callable) -> None:
    create(
        "ar.ics",
        f"UID:{uuid4()}\nSUMMARY:blah.ar\n"
        "DUE;VALUE=DATE-TIME;TZID=HST:20160102T000000\n",
    )
    create(
        "de.ics",
        f"UID:{uuid4()}\nSUMMARY:blah.de\n"
        "DUE;VALUE=DATE-TIME;TZID=CET:20160102T000000\n",
    )

    all_todos = list(todos())

    assert len(all_todos) == 2
    assert all_todos[0].due == datetime(2016, 1, 2, 0, 0, tzinfo=tzoffset(None, -36000))
    assert all_todos[1].due == datetime(2016, 1, 2, 0, 0, tzinfo=tzoffset(None, 3600))


def test_due_date(tmpdir: py.path.local, create: Callable, todos: Callable) -> None:
    create("ar.ics", "SUMMARY:blah.ar\nDUE;VALUE=DATE:20170617\n")

    all_todos = list(todos())

    assert len(all_todos) == 1
    assert all_todos[0].due == date(2017, 6, 17)


def test_change_paths(tmpdir: py.path.local, create: Callable) -> None:
    old_todos = set("abcdefghijk")
    for x in old_todos:
        create(f"{x}.ics", f"UID:{uuid4()}\nSUMMARY:{x}\n", x)

    tmpdir.mkdir("3")

    db = Database([tmpdir.join(x) for x in old_todos], tmpdir.join("cache.sqlite"))

    assert {t.summary for t in db.todos()} == old_todos

    db.paths = [str(tmpdir.join("3"))]
    db.update_cache()

    assert len(list(db.lists())) == 1
    assert not list(db.todos())


def test_list_displayname(tmpdir: py.path.local) -> None:
    tmpdir.join("default").mkdir()
    with tmpdir.join("default").join("displayname").open("w") as f:
        f.write("personal")

    db = Database([tmpdir.join("default")], tmpdir.join("cache.sqlite3"))
    list_ = next(db.lists())

    assert list_.name == "personal"
    assert str(list_) == "personal"


def test_list_colour(tmpdir: py.path.local) -> None:
    tmpdir.join("default").mkdir()
    with tmpdir.join("default").join("color").open("w") as f:
        f.write("#8ab6d2")

    db = Database([tmpdir.join("default")], tmpdir.join("cache.sqlite3"))
    list_ = next(db.lists())

    assert list_.colour == "#8ab6d2"


def test_list_colour_cache_invalidation(
    tmpdir: py.path.local,
    sleep: Callable[[], None],
) -> None:
    tmpdir.join("default").mkdir()
    with tmpdir.join("default").join("color").open("w") as f:
        f.write("#8ab6d2")

    db = Database([tmpdir.join("default")], tmpdir.join("cache.sqlite3"))
    list_ = next(db.lists())

    assert list_.colour == "#8ab6d2"

    sleep()

    with tmpdir.join("default").join("color").open("w") as f:
        f.write("#f874fd")

    db = Database([tmpdir.join("default")], tmpdir.join("cache.sqlite3"))
    list_ = next(db.lists())

    assert list_.colour == "#f874fd"


def test_list_no_colour(tmpdir: py.path.local) -> None:
    tmpdir.join("default").mkdir()

    db = Database([tmpdir.join("default")], tmpdir.join("cache.sqlite3"))
    list_ = next(db.lists())

    assert list_.colour is None


def test_database_priority_sorting(create: Callable, todos: Callable) -> None:
    for i in [1, 5, 9, 0]:
        create(f"test{i}.ics", f"UID:{uuid4()}\nPRIORITY:{i}\n")
    create("test_none.ics", f"UID:{uuid4()}\nSUMMARY:No priority (eg: None)\n")

    all_todos = list(todos())

    assert all_todos[0].priority == 0
    assert all_todos[1].priority == 0
    assert all_todos[2].priority == 9
    assert all_todos[3].priority == 5
    assert all_todos[4].priority == 1


def test_retain_unknown_fields(
    tmpdir: py.path.local,
    create: Callable,
    default_database: Database,
) -> None:
    """
    Test that we retain unknown fields after a load/save cycle.
    """
    create("test.ics", "UID:AVERYUNIQUEID\nSUMMARY:RAWR\nX-RAWR-TYPE:Reptar\n")

    db = Database([tmpdir.join("default")], tmpdir.join("cache.sqlite"))
    todo = db.todo(1, read_only=False)

    todo.description = 'Rawr means "I love you" in dinosaur.'
    default_database.save(todo)

    path = tmpdir.join("default").join("test.ics")
    with path.open() as f:
        vtodo = f.read()
    lines = vtodo.splitlines()

    assert "SUMMARY:RAWR" in lines
    assert 'DESCRIPTION:Rawr means "I love you" in dinosaur.' in lines
    assert "X-RAWR-TYPE:Reptar" in lines


def test_category_integrity(
    tmpdir: py.path.local,
    create: Callable,
    default_database: Database,
) -> None:
    create("test.ics", "UID:AVERYUNIQUEID\nSUMMARY:RAWR\n")
    db = Database([tmpdir.join("default")], tmpdir.join("cache.sqlite"))

    todo = db.todo(1, read_only=False)
    todo.categories = ["hi", "hi"]

    with pytest.raises(AlreadyExistsError):
        default_database.save(todo)


def test_category_deletes_on_todo_delete(
    tmpdir: py.path.local,
    create: Callable,
    default_database: Database,
) -> None:
    uid = "my_id"
    create("test.ics", f"UID:{uid}\nSUMMARY:RAWR\n")
    db = Database([tmpdir.join("default")], tmpdir.join("cache.sqlite"))

    todo = db.todo(1, read_only=False)
    todo.categories = ["my_cat"]
    default_database.save(todo)

    assert next(default_database.todos()).uid == uid

    default_database.delete(todo)
    default_database.update_cache()

    query = f"""
        SELECT distinct category
        FROM categories
        WHERE categories.todos_id = '{todo.id}'
        """

    categories = default_database.cache._conn.execute(query).fetchall()
    assert categories == []


def test_todo_setters(todo_factory: Callable) -> None:
    todo = todo_factory()

    todo.description = "A tea would be nice, thanks."
    assert todo.description == "A tea would be nice, thanks."

    todo.priority = 7
    assert todo.priority == 7

    now = datetime.now()
    todo.due = now
    assert todo.due == now

    todo.description = None
    assert todo.description == ""

    todo.priority = None
    assert todo.priority == 0

    todo.categories = None
    assert todo.categories == []

    todo.due = None
    assert todo.due is None


@freeze_time("2017-03-19-15")
def test_is_completed() -> None:
    completed_at = datetime(2017, 3, 19, 14, tzinfo=pytz.UTC)

    todo = Todo()
    assert todo.is_completed is False

    todo.completed_at = completed_at
    assert todo.is_completed is True

    todo.percent_complete = 20
    todo.complete()
    assert todo.is_completed is True
    assert todo.completed_at == datetime.now(pytz.UTC)
    assert todo.percent_complete == 100
    assert todo.status == "COMPLETED"


@pytest.mark.parametrize(
    "until",
    ["20990315T020000Z", "20990315T020000"],  # TZ-aware UNTIL  # TZ-naive UNTIL
)
@pytest.mark.parametrize("tz", [pytz.UTC, None])  # TZ-aware todos  # TZ-naive todos
@pytest.mark.parametrize("is_due", [True, False])
def test_complete_recurring(
    default_database: Database,
    is_due: bool,
    todo_factory: Callable,
    tz: tzinfo,
    until: str,
) -> None:
    # We'll lose the milis when casting, so:
    now = datetime.now(tz).replace(microsecond=0)

    if bool(tz) != bool(until.endswith("Z")):
        pytest.skip("These combinations are invalid, as per the spec.")

    original_start = now
    original_due = now + timedelta(hours=12) if is_due else None

    rrule = f"FREQ=DAILY;UNTIL={until}"
    todo = todo_factory(rrule=rrule, due=original_due, start=original_start)

    todo.complete()
    related = todo.related[0]

    if original_due:
        assert todo.due == original_due
    else:
        assert todo.due is None
    assert todo.start == original_start
    assert todo.is_completed
    assert not todo.rrule

    if original_due:
        assert related.due == original_due + timedelta(days=1)
    else:
        assert related.due is None
    assert related.start == original_start + timedelta(days=1)
    # check due/start tz
    assert not related.is_completed
    assert related.rrule == rrule


def test_save_recurring_related(
    default_database: Database,
    todo_factory: Callable,
    todos: Callable,
) -> None:
    now = datetime.now(pytz.UTC)
    original_due = now + timedelta(hours=12)
    rrule = "FREQ=DAILY;UNTIL=20990315T020000Z"
    todo = todo_factory(rrule=rrule, due=original_due)
    todo.complete()

    default_database.save(todo)

    all_todos = todos(status="ANY")
    todo = next(all_todos)
    assert todo.percent_complete == 100
    assert todo.is_completed is True
    assert not todo.rrule

    todo = next(all_todos)
    assert todo.percent_complete == 0
    assert todo.is_completed is False
    assert todo.rrule == rrule


def test_save_recurring_related_with_date(
    default_database: Database,
    todo_factory: Callable,
    todos: Callable,
) -> None:
    now = date.today()
    original_due = now + timedelta(days=1)
    rrule = "FREQ=DAILY;UNTIL=20990315"
    todo = todo_factory(rrule=rrule, due=original_due)
    todo.complete()

    default_database.save(todo)

    all_todos = todos(status="ANY")
    todo = next(all_todos)
    assert todo.percent_complete == 100
    assert todo.is_completed is True
    assert not todo.rrule

    todo = next(all_todos)
    assert todo.percent_complete == 0
    assert todo.is_completed is False
    assert todo.rrule == rrule


def test_todo_filename_absolute_path() -> None:
    Todo(filename="test.ics")
    with pytest.raises(ValueError, match="Must not be an absolute path: /test.ics"):
        Todo(filename="/test.ics")


def test_list_equality(tmpdir: py.path.local) -> None:
    list1 = TodoList(path=str(tmpdir), name="test list")
    list2 = TodoList(path=str(tmpdir), name="test list")
    list3 = TodoList(path=str(tmpdir), name="yet another test list")

    assert list1 == list2
    assert list1 != list3
    assert list1 != "test list"


def test_clone() -> None:
    now = datetime.now(tz=tzlocal())

    todo = Todo(new=True)
    todo.summary = "Organize a party"
    todo.location = "Home"
    todo.due = now
    todo.uid = "123"
    todo.id = 123
    todo.filename = "123.ics"

    clone = todo.clone()

    assert todo.summary == clone.summary
    assert todo.location == clone.location
    assert todo.due == clone.due
    assert todo.uid != clone.uid
    assert len(clone.uid) > 32
    assert clone.id is None
    assert todo.filename != clone.filename
    assert clone.uid in clone.filename


@freeze_time("2017, 3, 20")
def test_todos_startable(
    tmpdir: py.path.local,
    runner: CliRunner,
    todo_factory: Callable,
    todos: Callable,
) -> None:
    todo_factory(summary="started", start=datetime(2017, 3, 15))
    todo_factory(summary="nostart")
    todo_factory(summary="unstarted", start=datetime(2017, 3, 24))

    all_todos = list(todos(startable=True))

    assert len(all_todos) == 2
    for todo in all_todos:
        assert "unstarted" not in todo.summary


def test_filename_uid_colision(
    create: Callable,
    default_database: Database,
    runner: CliRunner,
    todos: Callable,
) -> None:
    create("ABC.ics", "SUMMARY:My UID is not ABC\nUID:NOTABC\n")
    assert len(list(todos())) == 1

    todo = Todo(new=False)
    todo.uid = "ABC"
    todo.list = next(default_database.lists())
    default_database.save(todo)

    assert len(list(todos())) == 2


def test_hide_cancelled(todos: Callable, todo_factory: Callable) -> None:
    todo_factory(status="CANCELLED")

    assert len(list(todos())) == 0
    assert len(list(todos(status="ANY"))) == 1


def test_illegal_start_suppression(
    create: Callable,
    default_database: Database,
    todos: Callable,
) -> None:
    create(
        "test.ics",
        "SUMMARY:Start doing stuff\n"
        "DUE;VALUE=DATE-TIME;TZID=CET:20170331T120000\n"
        "DTSTART;VALUE=DATE-TIME;TZID=CET:20170331T140000\n",
    )
    todo = next(todos())
    assert todo.start is None
    assert todo.due == datetime(2017, 3, 31, 12, tzinfo=tzoffset(None, 7200))


def test_default_status(create: Callable, todos: Callable) -> None:
    create("test.ics", "SUMMARY:Finish all these status tests\n")
    todo = next(todos())
    assert todo.status == "NEEDS-ACTION"


def test_nullify_field(
    default_database: Database,
    todo_factory: Callable,
    todos: Callable,
) -> None:
    todo_factory(due=datetime.now())

    todo = next(todos(status="ANY"))
    assert todo.due is not None

    todo.due = None
    default_database.save(todo)

    todo = next(todos(status="ANY"))
    assert todo.due is None


def test_duplicate_list(tmpdir: py.path.local) -> None:
    tmpdir.join("personal1").mkdir()
    with tmpdir.join("personal1").join("displayname").open("w") as f:
        f.write("personal")

    tmpdir.join("personal2").mkdir()
    with tmpdir.join("personal2").join("displayname").open("w") as f:
        f.write("personal")

    with pytest.raises(AlreadyExistsError):
        Database(
            [tmpdir.join("personal1"), tmpdir.join("personal2")],
            tmpdir.join("cache.sqlite3"),
        )


def test_unreadable_ics(
    todo_factory: Callable,
    todos: Callable,
    tmpdir: py.path.local,
) -> None:
    """
    Test that we properly handle an unreadable ICS file

    In this case, it's a directory, which will
    fail even if you run the tests as root (you shouldn't!!), but the same
    codepath is followed for readonly files, etc.
    """
    tmpdir.join("default").join("fake.ics").mkdir()
    todo_factory()

    with patch("logging.Logger.exception") as mocked_exception:
        all_todos = list(todos())

    assert len(all_todos) == 1
    assert mocked_exception.call_count == 1


def test_deleting_todo_without_list_fails(
    tmpdir: py.path.local,
    default_database: Database,
) -> None:
    db = Database([tmpdir.join("default")], tmpdir.join("cache.sqlite3"))
    todo = Todo()

    with pytest.raises(ValueError, match="Cannot delete Todo without a list."):
        db.delete(todo)


def test_saving_todo_without_list_fails(
    tmpdir: py.path.local,
    default_database: Database,
) -> None:
    db = Database([tmpdir.join("default")], tmpdir.join("cache.sqlite3"))
    todo = Todo()

    with pytest.raises(ValueError, match="Cannot save Todo without a list."):
        db.save(todo)


def test_todo_path_without_list(tmpdir: py.path.local) -> None:
    todo = Todo()

    with pytest.raises(ValueError, match="A todo without a list does not have a path."):
        todo.path  # noqa: B018  # expression raises
