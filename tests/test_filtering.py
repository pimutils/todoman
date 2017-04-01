from datetime import datetime, timedelta

from todoman.cli import cli
from todoman.model import Database, Todo


def test_priority(tmpdir, runner, create):
    result = runner.invoke(cli, ['list'], catch_exceptions=False)
    assert not result.exception
    assert not result.output.strip()

    create(
        'one.ics',
        'SUMMARY:haha\n'
        'PRIORITY:4\n'
    )
    create(
        'two.ics',
        'SUMMARY:hoho\n'
        'PRIORITY:9\n'
    )
    create(
        'three.ics',
        'SUMMARY:hehe\n'
        'PRIORITY:5\n'
    )
    create(
        'four.ics',
        'SUMMARY:huhu\n'
    )

    result_high = runner.invoke(cli, ['list', '--priority=high'])
    assert not result_high.exception
    assert 'haha' in result_high.output
    assert 'hoho' not in result_high.output
    assert 'huhu' not in result_high.output
    assert 'hehe' not in result_high.output

    result_medium = runner.invoke(cli, ['list', '--priority=medium'])
    assert not result_medium.exception
    assert 'haha' in result_medium.output
    assert 'hehe' in result_medium.output
    assert 'hoho' not in result_medium.output
    assert 'huhu' not in result_medium.output

    result_low = runner.invoke(cli, ['list', '--priority=low'])
    assert not result_low.exception
    assert 'haha' in result_low.output
    assert 'hehe' in result_low.output
    assert 'hoho' in result_low.output
    assert 'huhu' not in result_low.output

    result_none = runner.invoke(cli, ['list', '--priority=none'])
    assert not result_none.exception
    assert 'haha' in result_none.output
    assert 'hehe' in result_none.output
    assert 'hoho' in result_none.output
    assert 'huhu' in result_none.output

    result_error = runner.invoke(cli, ['list', '--priority=blah'])
    assert result_error.exception


def test_location(tmpdir, runner, create):
    result = runner.invoke(cli, ['list'], catch_exceptions=False)
    assert not result.exception
    assert not result.output.strip()

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
    assert not result.output.strip()

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
    assert not result.output.strip()

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


def test_due_aware(tmpdir, runner, create, now_for_tz):
    db = Database([tmpdir.join('default')], tmpdir.join('cache.sqlite'))
    l = next(db.lists())

    for tz in ['CET', 'HST']:
        for i in [1, 23, 25, 48]:
            todo = Todo(new=True)
            todo.due = now_for_tz(tz) + timedelta(hours=i)
            todo.summary = '{}'.format(i)

            todo.list = l
            db.save(todo)

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


def test_filtering_start(tmpdir, runner, todo_factory):
    today = datetime.now()
    now = today.strftime("%Y-%m-%d")

    tomorrow = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday = (today + timedelta(days=-1)).strftime("%Y-%m-%d")

    result = runner.invoke(cli, ['list', '--start', 'before', now])
    assert not result.exception
    assert not result.output.strip()

    result = runner.invoke(cli, ['list', '--start', 'after', now])
    assert not result.exception
    assert not result.output.strip()

    todo_factory(summary='haha', start=today)
    todo_factory(summary='hoho', start=today)
    todo_factory(summary='hihi', start=today - timedelta(days=2))
    todo_factory(summary='huhu')

    result = runner.invoke(cli, ['list', '--start', 'after', yesterday])
    assert not result.exception
    assert 'haha' in result.output
    assert 'hoho' in result.output
    assert 'hihi' not in result.output
    assert 'huhu' not in result.output

    result = runner.invoke(cli, ['list', '--start', 'before', yesterday])
    assert not result.exception
    assert 'haha' not in result.output
    assert 'hoho' not in result.output
    assert 'hihi' in result.output
    assert 'huhu' not in result.output

    result = runner.invoke(cli, ['list', '--start', 'after', tomorrow])
    assert not result.exception
    assert 'haha' not in result.output
    assert 'hoho' not in result.output
    assert 'hihi' not in result.output
    assert 'huhu' not in result.output


def test_statuses(todo_factory, todos):
    cancelled = todo_factory(status='CANCELLED').uid
    completed = todo_factory(status='COMPLETED').uid
    in_process = todo_factory(status='IN-PROCESS').uid
    needs_action = todo_factory(status='NEEDS-ACTION').uid
    no_status = todo_factory(status='NEEDS-ACTION').uid

    all_todos = set(todos(status=['ANY']))
    cancelled_todos = set(todos(status=['CANCELLED']))
    completed_todos = set(todos(status=['COMPLETED']))
    in_process_todos = set(todos(status=['IN-PROCESS']))
    needs_action_todos = set(todos(status=['NEEDS-ACTION']))

    assert {t.uid for t in all_todos} == {
        cancelled,
        completed,
        in_process,
        needs_action,
        no_status
    }
    assert {t.uid for t in cancelled_todos} == {cancelled}
    assert {t.uid for t in completed_todos} == {completed}
    assert {t.uid for t in in_process_todos} == {in_process}
    assert {t.uid for t in needs_action_todos} == {needs_action, no_status}
