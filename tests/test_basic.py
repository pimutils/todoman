from todoman.cli import cli


def test_basic(tmpdir, runner):
    result = runner.invoke(cli, ['list'], catch_exceptions=False)
    assert not result.exception
    assert result.output == ''

    foobar = tmpdir.mkdir('foobar')

    result = runner.invoke(cli, ['list'])
    assert not result.exception
    assert result.output == ''

    foobar.join('test.ics').write(
        'BEGIN:VCALENDAR\n'
        'BEGIN:VTODO\n'
        'SUMMARY:harhar\n'
        'END:VTODO\n'
        'END:VCALENDAR'
    )
    result = runner.invoke(cli, ['list'])
    assert not result.exception
    assert 'harhar' in result.output
