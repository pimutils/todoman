from todoman.cli import cli


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
