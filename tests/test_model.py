from datetime import datetime

import icalendar
import pytest
import pytz
from dateutil.tz import tzlocal
from dateutil.tz.tz import tzoffset
from freezegun import freeze_time

from todoman.model import Database, List, Todo


def test_querying(create, tmpdir):
    for list in 'abc':
        for i, location in enumerate('abc'):
            create(
                'test{}.ics'.format(i),
                ('SUMMARY:test_querying\r\n'
                 'LOCATION:{}\r\n').format(location),
                list_name=list
            )

    db = Database(
        [str(tmpdir.ensure_dir(l)) for l in 'abc'],
        str(tmpdir.join('cache'))
    )

    assert len(set(db.todos())) == 9
    assert len(set(db.todos(lists='ab'))) == 6
    assert len(set(db.todos(lists='ab', location='a'))) == 2


def test_retain_tz(tmpdir, create, default_database):
    create(
        'ar.ics',
        'SUMMARY:blah.ar\n'
        'DUE;VALUE=DATE-TIME;TZID=HST:20160102T000000\n'
    )
    create(
        'de.ics',
        'SUMMARY:blah.de\n'
        'DUE;VALUE=DATE-TIME;TZID=CET:20160102T000000\n'
    )

    db = Database([tmpdir.join('default')], tmpdir.join('cache.sqlite'))
    todos = list(db.todos())

    assert len(todos) == 2
    assert todos[0].due == datetime(
        2016, 1, 2, 0, 0, tzinfo=tzoffset(None, -36000)
    )
    assert todos[1].due == datetime(
        2016, 1, 2, 0, 0, tzinfo=tzoffset(None, 3600)
    )


def test_change_paths(tmpdir, create):
    old_todos = set('abcdefghijk')
    for x in old_todos:
        create('{}.ics'.format(x), 'SUMMARY:{}\n'.format(x), x)

    tmpdir.mkdir('3')

    db = Database([tmpdir.join(x) for x in old_todos],
                  tmpdir.join('cache.sqlite'))

    assert {t.summary for t in db.todos()} == old_todos

    db.paths = [str(tmpdir.join('3'))]
    db.update_cache()

    assert len(list(db.lists())) == 1
    assert not list(db.todos())


def test_sequence_increment(tmpdir, default_database):
    todo = Todo(new=True, list=next(default_database.lists()))
    default_database.save(todo)

    with open(todo.path) as f:
        cal = icalendar.Calendar.from_ical(f.read())
    sequence, = [component.get("SEQUENCE", 0)
                 for component in cal.subcomponents
                 if component.name == "VTODO"]

    assert sequence == 1

    default_database.save(todo)

    with open(todo.path) as f:
        cal = icalendar.Calendar.from_ical(f.read())
    sequence, = [component.get("SEQUENCE", 0)
                 for component in cal.subcomponents
                 if component.name == "VTODO"]

    assert sequence == 2


def test_list_displayname(tmpdir):
    tmpdir.join('default').mkdir()
    with tmpdir.join('default').join('displayname').open('w') as f:
        f.write('personal')

    db = Database([tmpdir.join('default')], tmpdir.join('cache.sqlite3'))
    list_ = next(db.lists())

    assert list_.name == 'personal'
    assert str(list_) == 'personal'


def test_list_colour(tmpdir):
    tmpdir.join('default').mkdir()
    with tmpdir.join('default').join('color').open('w') as f:
        f.write('#8ab6d2')

    db = Database([tmpdir.join('default')], tmpdir.join('cache.sqlite3'))
    list_ = next(db.lists())

    assert list_.colour == '#8ab6d2'
    assert list_.color_rgb == (138, 182, 210)
    assert list_.color_ansi == '\x1b[38;2;138;182;210m'


def test_list_no_colour(tmpdir):
    tmpdir.join('default').mkdir()

    db = Database([tmpdir.join('default')], tmpdir.join('cache.sqlite3'))
    list_ = next(db.lists())

    assert list_.colour is None
    assert list_.color_rgb is None
    assert list_.color_ansi is None


def test_database_priority_sorting(create, default_database):
    for i in [1, 5, 9, 0]:
        create(
            'test{}.ics'.format(i),
            'PRIORITY:{}\n'.format(i)
        )
    create(
        'test_none.ics'.format(i),
        'SUMMARY:No priority (eg: None)\n'
    )

    default_database.update_cache()
    todos = list(default_database.todos())

    assert todos[0].priority == 0
    assert todos[1].priority == 0
    assert todos[2].priority == 9
    assert todos[3].priority == 5
    assert todos[4].priority == 1


def test_retain_unknown_fields(tmpdir, create, default_database):
    """
    Test that we retain unknown fields after a load/save cycle.
    """
    create(
        'test.ics',
        'UID:AVERYUNIQUEID\n'
        'SUMMARY:RAWR\n'
        'X-RAWR-TYPE:Reptar\n'
    )

    db = Database([tmpdir.join('default')], tmpdir.join('cache.sqlite'))
    todo = db.todo(1, read_only=False)

    todo.description = 'Rawr means "I love you" in dinosaur.'
    default_database.save(todo)

    path = tmpdir.join('default').join('test.ics')
    with path.open() as f:
        vtodo = f.read()
    lines = vtodo.splitlines()

    assert 'SUMMARY:RAWR' in lines
    assert 'DESCRIPTION:Rawr means "I love you" in dinosaur.' in lines
    assert 'X-RAWR-TYPE:Reptar' in lines


def test_todo_setters(todo_factory):
    todo = todo_factory()

    todo.description = 'A tea would be nice, thanks.'
    assert todo.description == 'A tea would be nice, thanks.'

    todo.priority = 7
    assert todo.priority == 7

    now = datetime.now()
    todo.due = now
    assert todo.due == now

    todo.description = None
    assert todo.description == ''

    todo.priority = None
    assert todo.priority == 0

    todo.categories = None
    assert todo.categories == []

    todo.due = None
    assert todo.due is None


@freeze_time('2017-03-19-15')
def test_is_completed():
    completed_at = datetime(2017, 3, 19, 14, tzinfo=pytz.UTC),

    todo = Todo()
    todo.completed_at = completed_at
    todo.percent_complete = 20

    todo.is_completed = True
    assert todo.completed_at == completed_at
    assert todo.percent_complete == 100
    assert todo.status == 'COMPLETED'

    todo.is_completed = False
    assert todo.completed_at is None
    assert todo.percent_complete == 0
    assert todo.status == 'NEEDS-ACTION'

    todo.is_completed = True
    now = datetime(2017, 3, 19, 15, tzinfo=pytz.UTC).astimezone(tzlocal())
    assert todo.completed_at == now
    assert todo.percent_complete == 100
    assert todo.status == 'COMPLETED'


def test_todo_filename_absolute_path():
    Todo(filename='test.ics')
    with pytest.raises(ValueError):
        Todo(filename='/test.ics')


def test_list_equality(tmpdir):
    list1 = List(path=str(tmpdir), name='test list')
    list2 = List(path=str(tmpdir), name='test list')
    list3 = List(path=str(tmpdir), name='yet another test list')

    assert list1 == list2
    assert list1 != list3
    assert list1 != 'test list'


def test_clone():
    now = datetime.now(tz=tzlocal())

    todo = Todo(new=True)
    todo.summary = 'Organize a party'
    todo.location = 'Home'
    todo.due = now
    todo.uid = '123'
    todo.id = '123'
    todo.filename = '123.ics'

    clone = todo.clone()

    assert todo.summary == clone.summary
    assert todo.location == clone.location
    assert todo.due == clone.due
    assert todo.uid != clone.uid
    assert len(clone.uid) > 32
    assert clone.id is None
    assert todo.filename != clone.filename
    assert clone.uid in clone.filename


@freeze_time('2017, 3, 20')
def test_todos_today(tmpdir, runner, todo_factory, default_database):
    todo_factory(summary='started', start=datetime(2017, 3, 15))
    todo_factory(summary='nostart')
    todo_factory(summary='unstarted', start=datetime(2017, 3, 24))

    todos = list(default_database.todos(today=True))

    assert len(todos) == 2
    for todo in todos:
        assert 'unstarted' not in todo.summary


def test_filename_uid_colision(create, default_database, runner):
    create(
        'ABC.ics',
        'SUMMARY:My UID is not ABC\n'
        'UID:NOTABC\n'
    )
    default_database.update_cache()
    len(list(default_database.todos())) == 1

    todo = Todo(new=False)
    todo.uid = 'ABC'
    todo.list = next(default_database.lists())
    default_database.save(todo)

    default_database.update_cache()
    len(list(default_database.todos())) == 2
