import datetime

import hypothesis.strategies as st
import pytest
import pytz
from hypothesis import given

from todoman.cli import cli
from todoman.model import Database, Todo


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

    db = Database(str(tmpdir + '/default'))
    todo = list(db.todos.values())[0]
    assert todo.dtstamp is not None
    assert todo.dtstamp.tzinfo is pytz.utc


def test_default_list(tmpdir, runner, create):
    """
    Test the default_list config parameter
    """
    result = runner.invoke(cli, ['new', 'test default list'])
    assert result.exception

    path = tmpdir.join('config')
    path.write('default_list = default\n', 'a')

    result = runner.invoke(cli, ['new', 'test default list'])
    assert not result.exception

    db = Database(str(tmpdir + '/default'))
    todo = list(db.todos.values())[0]
    assert todo.summary == 'test default list'


def test_sorting_fields(tmpdir, runner, default_database):
    tasks = []
    for i in range(1, 10):
        days = datetime.timedelta(days=i)

        todo = Todo()
        todo.due = datetime.datetime.now() + days
        todo.created_at = datetime.datetime.now() - days
        todo.summary = 'harhar{}'.format(i)
        tasks.append(todo)

        default_database.save(todo)

    fields = tuple(field for field in dir(Todo) if not
                   field.startswith('_'))

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


@pytest.mark.parametrize('hours', [1, -1])
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
    if hours == 1:
        assert result.output == \
            ' 1 [ ]   {} aaa @default\x1b[0m\n'.format(due_str)
    else:
        assert result.output == \
            ' 1 [ ]   \x1b[31m{}\x1b[0m aaa @default\x1b[0m\n'.format(due_str)


# TODO: test aware/naive datetime sorting
# TODO: test --grep
