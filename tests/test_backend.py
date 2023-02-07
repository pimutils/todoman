from datetime import date
from datetime import datetime

import icalendar
import pytest
import pytz
from dateutil.tz import tzlocal
from freezegun import freeze_time

from todoman.model import Todo
from todoman.model import VtodoWriter


def test_datetime_serialization(todo_factory, tmpdir):
    now = datetime(2017, 8, 31, 23, 49, 53, tzinfo=pytz.UTC)
    todo = todo_factory(created_at=now)
    filename = tmpdir.join("default").join(todo.filename)
    with open(str(filename)) as f:
        assert "CREATED:20170831T234953Z\n" in f.readlines()


def test_serialize_created_at(todo_factory):
    now = datetime.now(tz=pytz.UTC)
    todo = todo_factory(created_at=now)
    vtodo = VtodoWriter(todo).serialize()

    assert vtodo.get("created") is not None


def test_serialize_dtstart(todo_factory):
    now = datetime.now(tz=pytz.UTC)
    todo = todo_factory(start=now)
    vtodo = VtodoWriter(todo).serialize()

    assert vtodo.get("dtstart") is not None


def test_serializer_raises(todo_factory):
    todo = todo_factory()
    writter = VtodoWriter(todo)

    with pytest.raises(Exception, match="Unknown field nonexistant"):
        writter.serialize_field("nonexistant", 7)


def test_supported_fields_are_serializeable():
    supported_fields = set(Todo.ALL_SUPPORTED_FIELDS)
    serialized_fields = set(VtodoWriter.FIELD_MAP.keys())

    assert supported_fields == serialized_fields


def test_vtodo_serialization(todo_factory):
    """Test VTODO serialization: one field of each type."""
    description = "A tea would be nice, thanks."
    todo = todo_factory(
        categories=["tea", "drinking", "hot"],
        description=description,
        due=datetime(3000, 3, 21),
        start=date(3000, 3, 21),
        priority=7,
        status="IN-PROCESS",
        summary="Some tea",
        rrule="FREQ=MONTHLY",
    )
    writer = VtodoWriter(todo)
    vtodo = writer.serialize()

    assert [str(c) for c in vtodo.get("categories").cats] == ["tea", "drinking", "hot"]
    assert str(vtodo.get("description")) == description
    assert vtodo.get("priority") == 7
    assert vtodo.decoded("due") == datetime(3000, 3, 21, tzinfo=tzlocal())
    assert vtodo.decoded("dtstart") == date(3000, 3, 21)
    assert str(vtodo.get("status")) == "IN-PROCESS"
    assert vtodo.get("rrule") == icalendar.vRecur.from_ical("FREQ=MONTHLY")


@freeze_time("2017-04-04 20:11:57")
def test_update_last_modified(todo_factory, todos, tmpdir):
    todo = todo_factory()
    assert todo.last_modified == datetime.now(tzlocal())


def test_sequence_increment(default_database, todo_factory, todos):
    todo = todo_factory()
    assert todo.sequence == 1

    default_database.save(todo)
    assert todo.sequence == 2

    # Relaod (and check the caching flow for the sequence)
    todo = next(todos())
    assert todo.sequence == 2


def test_normalize_datetime():
    writter = VtodoWriter(None)
    assert writter.normalize_datetime(date(2017, 6, 17)) == date(2017, 6, 17)
    assert writter.normalize_datetime(datetime(2017, 6, 17)) == datetime(
        2017, 6, 17, tzinfo=tzlocal()
    )
    assert writter.normalize_datetime(datetime(2017, 6, 17, 12, 19)) == datetime(
        2017, 6, 17, 12, 19, tzinfo=tzlocal()
    )
    assert writter.normalize_datetime(
        datetime(2017, 6, 17, 12, tzinfo=tzlocal())
    ) == datetime(2017, 6, 17, 12, tzinfo=tzlocal())
