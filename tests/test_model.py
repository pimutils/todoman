from datetime import datetime

import icalendar

from dateutil.tz.tz import tzoffset

from todoman.model import Database
from todoman.model import FileTodo
from todoman.model import List


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


def test_sequence_increment(tmpdir):
    default_dir = tmpdir.mkdir("default")

    todo = FileTodo()
    _list = List("default", str(default_dir))
    todo.save(_list)

    filename = default_dir.join(todo.filename)

    cal = icalendar.Calendar.from_ical(filename.read())
    sequence, = [component.get("SEQUENCE", 0)
                 for component in cal.subcomponents
                 if component.name == "VTODO"]

    assert sequence == 1

    todo.save(_list)

    cal = icalendar.Calendar.from_ical(filename.read())
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

    assert list_.color_raw == '#8ab6d2'
    assert list_.color_rgb == (138, 182, 210)
    assert list_.color_ansi == '\x1b[38;2;138;182;210m'


def test_list_no_colour(tmpdir):
    tmpdir.join('default').mkdir()

    db = Database([tmpdir.join('default')], tmpdir.join('cache.sqlite3'))
    list_ = next(db.lists())

    assert list_.color_raw is None
    assert list_.color_rgb is None
    assert list_.color_ansi is None
