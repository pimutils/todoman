from datetime import datetime, timedelta

import pytz
from dateutil.tz import tzlocal

from todoman.cli import cli
from todoman.model import Database, FileTodo


def test_all(tmpdir, runner, create):
    result = runner.invoke(cli, ['list'], catch_exceptions=False)
    assert not result.exception
    assert result.output == ''

    create(
        'one.ics',
        'SUMMARY:haha\n'
    )
    create(
        'two.ics',
        'SUMMARY:hoho\n'
        'PERCENT-COMPLETE:100\n'
        'STATUS:COMPLETED\n'
    )
    result = runner.invoke(cli, ['list', '--all'])
    assert not result.exception
    assert 'haha' in result.output
    assert 'hoho' in result.output


def test_urgent(tmpdir, runner, create):
    result = runner.invoke(cli, ['list'], catch_exceptions=False)
    assert not result.exception
    assert result.output == ''

    create(
        'one.ics',
        'SUMMARY:haha\n'
        'PRIORITY: 9\n'
    )
    create(
        'two.ics',
        'SUMMARY:hoho\n'
    )
    result = runner.invoke(cli, ['list', '--urgent'])
    assert not result.exception
    assert 'haha' in result.output
    assert 'hoho' not in result.output


def test_location(tmpdir, runner, create):
    result = runner.invoke(cli, ['list'], catch_exceptions=False)
    assert not result.exception
    assert result.output == ''

    create(
        'one.ics',
        'SUMMARY:haha\n'
        'LOCATION: The Pool\n'
    )
    create(
        'two.ics',
        'SUMMARY:hoho\n'
        'LOCATION: The Dungeon\n'
    )
    create(
        'two.ics',
        'SUMMARY:harhar\n'
    )
    result = runner.invoke(cli, ['list', '--location', 'Pool'])
    assert not result.exception
    assert 'haha' in result.output
    assert 'hoho' not in result.output
    assert 'harhar' not in result.output


def test_category(tmpdir, runner, create):
    result = runner.invoke(cli, ['list'], catch_exceptions=False)
    assert not result.exception
    assert result.output == ''

    create(
        'one.ics',
        'SUMMARY:haha\n'
        'CATEGORIES:work,trip\n'
    )
    create(
        'two.ics',
        'CATEGORIES:trip\n'
        'SUMMARY:hoho\n'
    )
    create(
        'three.ics',
        'SUMMARY:harhar\n'
    )
    result = runner.invoke(cli, ['list', '--category', 'work'])
    assert not result.exception
    assert 'haha' in result.output
    assert 'hoho' not in result.output
    assert 'harhar' not in result.output


def test_grep(tmpdir, runner, create):
    result = runner.invoke(cli, ['list'], catch_exceptions=False)
    assert not result.exception
    assert result.output == ''

    create(
        'one.ics',
        'SUMMARY:fun\n'
        'DESCRIPTION: Have fun!\n',
    )
    create(
        'two.ics',
        'SUMMARY:work\n'
        'DESCRIPTION: The stuff for work\n',
    )
    create(
        'three.ics',
        'SUMMARY:buy sandwiches\n'
        'DESCRIPTION: This is for the Duke\n',
    )
    create(
        'four.ics',
        'SUMMARY:puppies\n'
        'DESCRIPTION: Feed the puppies\n',
    )
    create(
        'five.ics',
        'SUMMARY:research\n'
        'DESCRIPTION: Cure cancer\n',
    )
    create(
        'six.ics',
        'SUMMARY:hoho\n'
    )
    result = runner.invoke(cli, ['list', '--grep', 'fun'])
    assert not result.exception
    assert 'fun' in result.output
    assert 'work' not in result.output
    assert 'sandwiches' not in result.output
    assert 'puppies' not in result.output
    assert 'research' not in result.output
    assert 'hoho' not in result.output


def test_filtering_lists(tmpdir, runner, create):
    tmpdir.mkdir('list_one')
    tmpdir.mkdir('list_two')
    tmpdir.mkdir('list_three')

    runner.invoke(cli, ['new', '-l', 'list_one', 'todo one'])
    runner.invoke(cli, ['new', '-l', 'list_two', 'todo two'])
    runner.invoke(cli, ['new', '-l', 'list_three', 'todo three'])

    result = runner.invoke(cli, ['new', 'list'])
    assert len(result.output.splitlines()) == 3

    result = runner.invoke(cli, ['list', 'list_two'])
    assert not result.exception
    assert len(result.output.splitlines()) == 1
    assert 'todo two' in result.output


def test_due_aware(tmpdir, runner, create):
    now = datetime.now()

    db = Database([tmpdir.join('default')], tmpdir.join('cache.sqlite'))
    l = next(db.lists())

    for tz in ['CET', 'HST']:
        for i in [1, 23, 25, 48]:
            todo = FileTodo()
            todo.due = (now + timedelta(hours=i)).replace(tzinfo=tzlocal()) \
                .astimezone(pytz.timezone(tz))
            todo.summary = '{}'.format(i)

            db.save(todo, l)

    todos = list(db.todos(due=24))

    assert len(todos) == 4
    assert todos[0].summary == "23"
    assert todos[1].summary == "23"
    assert todos[2].summary == "1"
    assert todos[3].summary == "1"


def test_due_naive(tmpdir, runner, create):
    now = datetime.now()

    for i in [1, 23, 25, 48]:
        due = now + timedelta(hours=i)
        create(
            'test_{}.ics'.format(i),
            'SUMMARY:{}\n'
            'DUE;VALUE=DATE-TIME:{}\n'.format(
                i, due.strftime("%Y%m%dT%H%M%S"),
            )
        )

    db = Database([tmpdir.join('default')], tmpdir.join('cache.sqlite'))
    todos = list(db.todos(due=24))

    assert len(todos) == 2
    assert todos[0].summary == "23"
    assert todos[1].summary == "1"
