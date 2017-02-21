import datetime

import hypothesis.strategies as st
import pytest
import pytz
from dateutil.tz import tzlocal
from freezegun import freeze_time
from hypothesis import given

from todoman.cli import cli
from todoman.model import Database, FileTodo


def test_basic(tmpdir, runner, create):
    result = runner.invoke(cli, ['list'], catch_exceptions=False)
    assert not result.exception
    assert result.output == ''

    create(
        'test.ics',
        'SUMMARY:harhar\n'
    )
    result = runner.invoke(cli, ['list'])
    assert not result.exception
    assert 'harhar' in result.output


def test_percent(tmpdir, runner, create):
    create(
        'test.ics',
        'SUMMARY:harhar\n'
        'PERCENT-COMPLETE:78\n'
    )
    result = runner.invoke(cli, ['list'])
    assert not result.exception
    assert '78%' in result.output


def test_list_inexistant(tmpdir, runner, create):
    result = runner.invoke(cli, ['list', 'nonexistant'])
    assert result.exception
    assert 'Error: Invalid value for "lists":' in result.output


def test_show_existing(tmpdir, runner, create):
    create(
        'test.ics',
        'SUMMARY:harhar\n'
        'DESCRIPTION:Lots of text. Yum!\n'
    )
    result = runner.invoke(cli, ['list'])
    result = runner.invoke(cli, ['show', '1'])
    assert not result.exception
    assert 'harhar' in result.output
    assert 'Lots of text. Yum!' in result.output


def test_show_inexistant(tmpdir, runner, create):
    create(
        'test.ics',
        'SUMMARY:harhar\n'
    )
    result = runner.invoke(cli, ['list'])
    result = runner.invoke(cli, ['show', '2'])
    assert result.exit_code == -2
    assert result.output == 'No todo with id 2.\n'


def test_human(runner):
    result = runner.invoke(cli, [
        'new', '-l', 'default', '-d', 'tomorrow', 'hail belzebub'
    ])
    assert not result.exception
    assert 'belzebub' in result.output

    result = runner.invoke(cli, ['list'])
    assert not result.exception
    assert 'belzebub' in result.output


@pytest.mark.xfail(reason='issue#9')
def test_two_events(tmpdir, runner):
    tmpdir.join('default/test.ics').write(
        'BEGIN:VCALENDAR\n'
        'BEGIN:VTODO\n'
        'SUMMARY:task one\n'
        'END:VTODO\n'
        'BEGIN:VTODO\n'
        'SUMMARY:task two\n'
        'END:VTODO\n'
        'END:VCALENDAR'
    )
    result = runner.invoke(cli, ['list'])
    assert not result.exception
    assert len(result.output.splitlines()) == 2
    assert 'task one' in result.output
    assert 'task two' in result.output


def test_default_command(tmpdir, runner, create):
    create(
        'test.ics',
        'SUMMARY:harhar\n'
    )
    result = runner.invoke(cli)
    assert not result.exception
    assert 'harhar' in result.output


def test_delete(tmpdir, runner, create):
    create(
        'test.ics',
        'SUMMARY:harhar\n'
    )
    result = runner.invoke(cli, ['list'])
    assert not result.exception
    result = runner.invoke(cli, ['delete', '1', '--yes'])
    assert not result.exception
    result = runner.invoke(cli, ['list'])
    assert not result.exception
    assert len(result.output.splitlines()) == 0


def test_copy(tmpdir, runner, create):
    tmpdir.mkdir('other_list')
    create(
        'test.ics',
        'SUMMARY:test_copy\n'
    )
    result = runner.invoke(cli, ['list'])
    assert not result.exception
    assert 'test_copy' in result.output
    assert 'default' in result.output
    assert 'other_list' not in result.output
    result = runner.invoke(cli, ['copy', '-l', 'other_list', '1'])
    assert not result.exception
    result = runner.invoke(cli, ['list'])
    assert not result.exception
    assert 'test_copy' in result.output
    assert 'default' in result.output
    assert 'other_list' in result.output


def test_move(tmpdir, runner, create):
    tmpdir.mkdir('other_list')
    create(
        'test.ics',
        'SUMMARY:test_move\n'
    )
    result = runner.invoke(cli, ['list'])
    assert not result.exception
    assert 'test_move' in result.output
    assert 'default' in result.output
    assert 'other_list' not in result.output
    result = runner.invoke(cli, ['move', '-l', 'other_list', '1'])
    assert not result.exception
    result = runner.invoke(cli, ['list'])
    assert not result.exception
    assert 'test_move' in result.output
    assert 'default' not in result.output
    assert 'other_list' in result.output


def test_dtstamp(tmpdir, runner, create):
    """
    Test that we add the DTSTAMP to new entries as per RFC5545.
    """
    result = runner.invoke(cli, ['new', '-l', 'default', 'test event'])
    assert not result.exception

    db = Database([tmpdir.join('default')],
                  tmpdir.join('/dtstamp_cache'))
    todo = list(db.todos())[0]
    assert todo.dtstamp is not None
    assert todo.dtstamp.tzinfo is pytz.utc


def test_default_list(tmpdir, runner, create):
    """Test the default_list config parameter"""
    result = runner.invoke(cli, ['new', 'test default list'])
    assert result.exception

    path = tmpdir.join('config')
    path.write('default_list = default\n', 'a')

    result = runner.invoke(cli, ['new', 'test default list'])
    assert not result.exception

    db = Database([tmpdir.join('default')],
                  tmpdir.join('/default_list'))
    todo = list(db.todos())[0]
    assert todo.summary == 'test default list'


@pytest.mark.parametrize(
    'default_due, expected_due_hours', [(None, 24), (1, 1), (0, None)],
    ids=['not specified', 'greater than 0', '0']
)
def test_default_due(
    tmpdir, runner, create, default_due, expected_due_hours
):
    """Test setting the due date using the default_due config parameter"""
    if default_due is not None:
        path = tmpdir.join('config')
        path.write('default_due = {}\n'.format(default_due), 'a')

    runner.invoke(cli, ['new', '-l', 'default', 'aaa'])
    db = Database([tmpdir.join('default')], tmpdir.join('/default_list'))
    todo = list(db.todos())[0]

    if expected_due_hours is None:
        assert todo.due is None
    else:
        assert (todo.due - todo.created_at) == datetime.timedelta(
            hours=expected_due_hours
        )


@freeze_time(datetime.datetime.now())
def test_default_due2(tmpdir, runner, create, default_database):
    cfg = tmpdir.join('config')
    cfg.write('default_due = 24\n', 'a')

    r = runner.invoke(cli, ['new', '-ldefault', '-dtomorrow', 'aaa'])
    assert not r.exception
    r = runner.invoke(cli, ['new', '-ldefault', 'bbb'])
    assert not r.exception
    r = runner.invoke(cli, ['new', '-ldefault', '-d', 'one hour', 'ccc'])
    assert not r.exception

    default_database.update_cache()
    todos = {t.summary: t for t in default_database.todos(all=True)}
    assert todos['aaa'].due.date() == todos['bbb'].due.date()
    assert todos['ccc'].due == todos['bbb'].due - datetime.timedelta(hours=23)


def test_sorting_fields(tmpdir, runner, default_database):
    tasks = []
    for i in range(1, 10):
        days = datetime.timedelta(days=i)

        todo = FileTodo(new=True)
        todo.list = next(default_database.lists())
        todo.due = datetime.datetime.now() + days
        todo.created_at = datetime.datetime.now() - days
        todo.summary = 'harhar{}'.format(i)
        tasks.append(todo)

        todo.save()

    fields = (
        'id',
        'uid',
        'summary',
        'due',
        'priority',
        'created_at',
        'completed_at',
        'dtstamp',
        'status',
        'description',
        'location',
        'categories',
    )

    @given(sort_key=st.lists(
        st.sampled_from(fields + tuple('-' + x for x in fields)),
        unique=True
    ))
    def run_test(sort_key):
        sort_key = ','.join(sort_key)
        result = runner.invoke(cli, ['list', '--sort', sort_key])
        assert not result.exception
        assert result.exit_code == 0
        assert len(result.output.strip().splitlines()) == len(tasks)

    run_test()


def test_sorting_output(tmpdir, runner, create):
    create(
        'test.ics',
        'SUMMARY:aaa\n'
        'DUE;VALUE=DATE-TIME;TZID=ART:20160102T000000\n'
    )
    create(
        'test2.ics',
        'SUMMARY:bbb\n'
        'DUE;VALUE=DATE-TIME;TZID=ART:20160101T000000\n'
    )

    examples = [
        ('-summary', ['aaa', 'bbb']),
        ('due', ['aaa', 'bbb'])
    ]

    # Normal sorting, reversed by default
    all_examples = [(['--sort', key], order) for key, order in examples]

    # Testing --reverse, same exact output
    all_examples.extend((['--reverse', '--sort', key], order)
                        for key, order in examples)

    # Testing --no-reverse
    all_examples.extend((['--no-reverse', '--sort', key], reversed(order))
                        for key, order in examples)

    for args, order in all_examples:
        result = runner.invoke(cli, ['list'] + args)
        assert not result.exception
        lines = result.output.splitlines()
        for i, task in enumerate(order):
            assert task in lines[i]


def test_sorting_null_values(tmpdir, runner, create):
    create(
        'test.ics',
        'SUMMARY:aaa\n'
        'PRIORITY:9\n'
    )
    create(
        'test2.ics',
        'SUMMARY:bbb\n'
        'DUE;VALUE=DATE-TIME;TZID=ART:20160101T000000\n'
    )

    result = runner.invoke(cli)
    assert not result.exception
    assert 'bbb' in result.output.splitlines()[0]
    assert 'aaa' in result.output.splitlines()[1]


@pytest.mark.parametrize('hours', [72, -72])
def test_color_due_dates(tmpdir, runner, create, hours):
    due = datetime.datetime.now() + datetime.timedelta(hours=hours)
    create(
        'test.ics',
        'SUMMARY:aaa\n'
        'STATUS:IN-PROGRESS\n'
        'DUE;VALUE=DATE-TIME;TZID=ART:{}\n'
        .format(due.strftime('%Y%m%dT%H%M%S'))
    )

    result = runner.invoke(cli, ['--color', 'always'])
    assert not result.exception
    due_str = due.strftime('%Y-%m-%d')
    if hours == 72:
        assert result.output == \
            '  1 [ ]   {} aaa @default\x1b[0m\n'.format(due_str)
    else:
        assert result.output == \
            '  1 [ ]   \x1b[31m{}\x1b[0m aaa @default\x1b[0m\n'.format(due_str)


def test_flush(tmpdir, runner, create):
    create(
        'test.ics',
        'SUMMARY:aaa\n'
        'STATUS:COMPLETED\n'
    )

    result = runner.invoke(cli, ['list'])
    assert not result.exception

    create(
        'test2.ics',
        'SUMMARY:bbb\n'
    )

    result = runner.invoke(cli, ['list'])
    assert not result.exception
    assert '  2 [ ]              bbb @default' in result.output

    result = runner.invoke(cli, ['flush'], input='y\n', catch_exceptions=False)
    assert not result.exception

    create(
        'test2.ics',
        'SUMMARY:bbb\n'
    )

    result = runner.invoke(cli, ['list'])
    assert not result.exception
    assert '  1 [ ]              bbb @default' in result.output


def test_edit(runner, default_database):
    todo = FileTodo()
    todo.list = next(default_database.lists())
    todo.summary = 'Eat paint'
    todo.due = datetime.datetime(2016, 10, 3)
    todo.save()

    result = runner.invoke(cli, ['edit', '1', '--due', '2017-02-01'])
    assert not result.exception
    assert '2017-02-01' in result.output

    default_database.update_cache()
    todo = next(default_database.todos(all=True))
    assert todo.due == datetime.datetime(2017, 2, 1, tzinfo=tzlocal())
    assert todo.summary == 'Eat paint'

# TODO: test aware/naive datetime sorting
# TODO: test --grep
