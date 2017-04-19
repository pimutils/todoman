from datetime import datetime

import icalendar
import pytest
import pytz
from dateutil.tz import tzlocal
from freezegun import freeze_time

from todoman.model import Todo, VtodoWritter


def test_serialize_created_at(todo_factory):
    now = datetime.now(tz=pytz.UTC)
    todo = todo_factory(created_at=now)
    vtodo = VtodoWritter(todo).serialize()

    assert vtodo.get('created') is not None


def test_serialize_dtstart(todo_factory):
    now = datetime.now(tz=pytz.UTC)
    todo = todo_factory(start=now)
    vtodo = VtodoWritter(todo).serialize()

    assert vtodo.get('dtstart') is not None


def test_serializer_raises(todo_factory):
    todo = todo_factory()
    writter = VtodoWritter(todo)

    with pytest.raises(Exception):
        writter.serialize_field('nonexistant', 7)


def test_supported_fields_are_serializeable():
    supported_fields = set(Todo.ALL_SUPPORTED_FIELDS)
    serialized_fields = set(VtodoWritter.FIELD_MAP.keys())

    assert supported_fields == serialized_fields


def test_vtodo_serialization(todo_factory):
    """Test VTODO serialization: one field of each type."""
    description = 'A tea would be nice, thanks.'
    todo = todo_factory(
        categories=['tea', 'drinking', 'hot'],
        description=description,
        due=datetime(3000, 3, 21),
        priority=7,
        status='IN-PROCESS',
        summary='Some tea',
        rrule='FREQ=MONTHLY',
    )
    writer = VtodoWritter(todo)
    vtodo = writer.serialize()

    assert str(vtodo.get('categories')) == 'tea,drinking,hot'
    assert str(vtodo.get('description')) == description
    assert vtodo.get('priority') == 7
    assert vtodo.decoded('due') == datetime(3000, 3, 21, tzinfo=tzlocal())
    assert str(vtodo.get('status')) == 'IN-PROCESS'
    assert vtodo.get('rrule') == icalendar.vRecur.from_ical('FREQ=MONTHLY')


@freeze_time('2017-04-04 20:11:57')
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
