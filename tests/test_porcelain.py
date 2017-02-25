from todoman.cli import cli


def test_list_all(tmpdir, runner, create):
    create(
        'test.ics',
        'SUMMARY:Do stuff\n'
        'STATUS:COMPLETED\n'
        'DUE;VALUE=DATE-TIME;TZID=CET:20160102T000000\n'
        'PERCENT-COMPLETE:26\n'
        'PRIORITY:0'
    )

    result = runner.invoke(cli, ['--porcelain', 'list', '--all'])
    assert (
        result.output.strip() ==
        '{"completed": true, "due": 1451689200, "id": 1, "list": "default'
        '", "percent": 26, "summary": "Do stuff", "priority": 0}'
    )


def test_list_nodue(tmpdir, runner, create):
    create(
        'test.ics',
        'SUMMARY:Do stuff\n'
        'PERCENT-COMPLETE:12\n'
        'PRIORITY:1\n'
    )

    result = runner.invoke(cli, ['--porcelain', 'list'])
    assert (
        result.output.strip() ==
        '{"completed": false, "due": null, "id": 1, "list": "default'
        '", "percent": 12, "summary": "Do stuff", "priority": 1}'
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
        '"default", "percent": 0, "summary": "harhar", "priority": 5}\n'
    )
