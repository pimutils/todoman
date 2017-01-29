import pytest
from click.testing import CliRunner

from todoman.cli import cli


def test_explicit_nonexistant(runner):
    result = CliRunner().invoke(
        cli,
        env={
            'TODOMAN_CONFIG': '/nonexistant',
        },
        catch_exceptions=True,
    )
    assert result.exception
    assert str(result.exception) == \
        "Configuration file /nonexistant does not exist"


@pytest.mark.xfail(reason='unknown')  # FIXME!
def test_xdg_nonexistant(runner):
    result = CliRunner().invoke(
        cli,
        env={
            'XDG_CONFIG_HOME': '/nonexistant',
        },
        catch_exceptions=True,
    )
    assert result.exception
    assert str(result.exception) == "No Configuration file found"


def test_sane_config(config, runner):
    config.write(
        '[main]\n'
        'color = "auto"\n'
        'date_format = "%Y-%m-%d"\n'
        'path = "/"\n'
    )
    result = runner.invoke(cli)
    assert not result.exception


def test_invalid_color(config, runner):
    config.write(
        '[main]\n'
        'color = 12\n'
        'path = "/"\n'
    )
    result = runner.invoke(cli, ['list'])
    assert result.exception
    assert "12 is not of type 'string'" in result.exception.args[0]


def test_missing_path(config, runner):
    config.write(
        '[main]\n'
        'color = "auto"\n'
    )
    result = runner.invoke(cli, ['list'])
    assert result.exception
    assert "'path' is a required property" in result.exception.args[0]


def test_extra_field(config, runner):
    config.write(
        '[main]\n'
        'color = "auto"\n'
        'date_format = "%Y-%m-%d"\n'
        'path = "/"\n'
        'blah = "false"\n'
    )
    result = runner.invoke(cli, ['list'])
    assert result.exception
    assert "Additional properties are not allowed" in result.exception.args[0]


def test_extra_table(config, runner):
    config.write(
        '[main]\n'
        'date_format = "%Y-%m-%d"\n'
        'path = "{}/*"\n'
        '[extra]\n'
        'color = "auto"\n'
    )
    result = runner.invoke(cli, ['list'])
    assert result.exception
    assert "Additional properties are not allowed" in result.exception.args[0]
