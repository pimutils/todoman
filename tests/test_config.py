import pytest
import xdg
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
    assert "Configuration file /nonexistant does not exist" in result.output


def test_xdg_nonexistant(runner):
    original_dirs = xdg.BaseDirectory.xdg_config_dirs
    xdg.BaseDirectory.xdg_config_dirs = []

    try:
        result = CliRunner().invoke(
            cli,
            catch_exceptions=True,
        )
        assert result.exception
        assert "No configuration file found" in result.output
    except:
        raise
    finally:
        # Make sure we ALWAYS set this back to the origianl value, even if the
        # test failed.
        xdg.BaseDirectory.xdg_config_dirs = original_dirs


def test_xdg_existant(runner, tmpdir, config):
    conf_path = tmpdir.mkdir('todoman')
    with conf_path.join('todoman.conf').open('w') as f:
        f.write(config.open().read())

    original_dirs = xdg.BaseDirectory.xdg_config_dirs
    xdg.BaseDirectory.xdg_config_dirs = [str(tmpdir)]

    try:
        result = CliRunner().invoke(
            cli,
            catch_exceptions=True,
        )
        assert not result.exception
        assert result.output == ''
    except:
        raise
    finally:
        # Make sure we ALWAYS set this back to the origianl value, even if the
        # test failed.
        xdg.BaseDirectory.xdg_config_dirs = original_dirs


def test_sane_config(config, runner, tmpdir):
    config.write(
        '[main]\n'
        'color = auto\n'
        'date_format = %Y-%m-%d\n'
        'path = /\n'
        'cache_path = {}\n'.format(tmpdir.join('cache.sqlite'))
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
    assert "Error: Invalid color setting: Choose from always, never, auto." \
        in result.output


def test_missing_path(config, runner):
    config.write(
        '[main]\n'
        'color = auto\n'
    )
    result = runner.invoke(cli, ['list'])
    assert result.exception
    assert ("Error: path is missing from the ['main'] section of the "
            "configuration file") in result.output


@pytest.mark.xfail(reason="Not implemented")
def test_extra_entry(config, runner):
    config.write(
        '[main]\n'
        'color = auto\n'
        'date_format = %Y-%m-%d\n'
        'path = /\n'
        'blah = false\n'
    )
    result = runner.invoke(cli, ['list'])
    assert result.exception
    assert "Invalid configuration entry" in result.output


@pytest.mark.xfail(reason="Not implemented")
def test_extra_section(config, runner):
    config.write(
        '[main]\n'
        'date_format = %Y-%m-%d\n'
        'path = /\n'
        '[extra]\n'
        'color = auto\n'
    )
    result = runner.invoke(cli, ['list'])
    assert result.exception
    assert "Invalid configuration section" in result.output
