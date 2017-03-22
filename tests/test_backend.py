from datetime import datetime

import pytest
import pytz

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
