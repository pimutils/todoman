from todoman.cli import cli


def test_list_all(tmpdir, runner, create):
    create(
        'test.ics',
        'SUMMARY:Do stuff\n'
        'STATUS:COMPLETED\n'
        'DUE;VALUE=DATE-TIME;TZID=CET:20160102T000000\n'
        'PERCENT-COMPLETE:26\n'
    )

    result = runner.invoke(cli, ['--porcelain', 'list', '--all'])
    assert not result.exception
    assert (
        result.output.strip() ==
        '{"completed": true, "due": 1451689200, "id": 1, "list": "default'
        '", "percent": 26, "priority": 0, "summary": "Do stuff"}'
    )


def test_list_nodue(tmpdir, runner, create):
    create(
        'test.ics',
        'SUMMARY:Do stuff\n'
        'PERCENT-COMPLETE:12\n'
        'PRIORITY:4\n'
    )

    result = runner.invoke(cli, ['--porcelain', 'list'])
    assert not result.exception
    assert (
        result.output.strip() ==
        '{"completed": false, "due": null, "id": 1, "list": "default'
        '", "percent": 12, "priority": 4, "summary": "Do stuff"}'
    )


def test_show(tmpdir, runner, create):
    create(
        'test.ics',
        'SUMMARY:harhar\n'
        'DESCRIPTION:Lots of text. Yum!\n'
        'PRIORITY:5\n'
    )
    result = runner.invoke(cli, ['--porcelain', 'show', '1'])
    assert not result.exception
    assert (
        result.output == '{"completed": false, "due": null, "id": 1, "list": '
        '"default", "percent": 0, "priority": 5, "summary": "harhar"}\n'
    )
