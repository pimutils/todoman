import pytest

from todoman.cli import cli


def test_basic(tmpdir, runner):
    result = runner.invoke(cli, ['list'], catch_exceptions=False)
    assert not result.exception
    assert result.output == ''

    tmpdir.join('default/test.ics').write(
        'BEGIN:VCALENDAR\n'
        'BEGIN:VTODO\n'
        'SUMMARY:harhar\n'
        'END:VTODO\n'
        'END:VCALENDAR'
    )
    result = runner.invoke(cli, ['list'])
    assert not result.exception
    assert 'harhar' in result.output


def test_percent(tmpdir, runner):
    tmpdir.join('default/test.ics').write(
        'BEGIN:VCALENDAR\n'
        'BEGIN:VTODO\n'
        'SUMMARY:harhar\n'
        'PERCENT-COMPLETE:78\n'
        'END:VTODO\n'
        'END:VCALENDAR'
    )
    result = runner.invoke(cli, ['list'])
    assert not result.exception
    assert '78%' in result.output


def test_show_existing(tmpdir, runner):
    tmpdir.join('default/test.ics').write(
        'BEGIN:VCALENDAR\n'
        'BEGIN:VTODO\n'
        'SUMMARY:harhar\n'
        'DESCRIPTION:Lots of text. Yum!\n'
        'END:VTODO\n'
        'END:VCALENDAR'
    )
    result = runner.invoke(cli, ['list'])
    result = runner.invoke(cli, ['show', '1'])
    assert not result.exception
    assert 'harhar' in result.output
    assert 'Lots of text. Yum!' in result.output


def test_show_inexistant(tmpdir, runner):
    tmpdir.join('default/test.ics').write(
        'BEGIN:VCALENDAR\n'
        'BEGIN:VTODO\n'
        'SUMMARY:harhar\n'
        'END:VTODO\n'
        'END:VCALENDAR'
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


def test_default_command(tmpdir, runner):
    tmpdir.join('default/test.ics').write(
        'BEGIN:VCALENDAR\n'
        'BEGIN:VTODO\n'
        'SUMMARY:harhar\n'
        'END:VTODO\n'
        'END:VCALENDAR'
    )
    result = runner.invoke(cli)
    assert not result.exception
    assert 'harhar' in result.output


# TODO: test aware/naive datetime sorting
# TODO: test --grep
