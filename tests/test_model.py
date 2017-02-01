from datetime import datetime

from dateutil.tz.tz import tzoffset

from todoman.model import Database


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


def test_retain_tz(tmpdir, runner, create, default_database):
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
