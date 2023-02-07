from unittest.mock import patch

import pytest
from click.testing import CliRunner

from todoman.cli import cli
from todoman.configuration import ConfigurationError
from todoman.configuration import load_config


def test_explicit_nonexistant(runner):
    result = CliRunner().invoke(
        cli,
        env={"TODOMAN_CONFIG": "/nonexistant"},
        catch_exceptions=True,
    )
    assert result.exception
    assert "Configuration file /nonexistant does not exist" in result.output


def test_xdg_nonexistant(runner):
    with patch("xdg.BaseDirectory.xdg_config_dirs", ["/does-not-exist"]):
        result = CliRunner().invoke(
            cli,
            catch_exceptions=True,
        )
        assert result.exception
        assert "No configuration file found" in result.output


def test_xdg_existant(runner, tmpdir, config):
    with tmpdir.mkdir("todoman").join("config.py").open("w") as f, config.open() as c:
        f.write(c.read())

    with patch("xdg.BaseDirectory.xdg_config_dirs", [str(tmpdir)]):
        result = CliRunner().invoke(
            cli,
            catch_exceptions=True,
        )
        assert not result.exception
        assert not result.output.strip()


def test_sane_config(config, runner, tmpdir):
    config.write(
        'color = "auto"\n'
        'date_format = "%Y-%m-%d"\n'
        f'path = "{tmpdir}"\n'
        f'cache_path = "{tmpdir.join("cache.sqlite")}"\n'
    )
    result = runner.invoke(cli)
    # This is handy for debugging breakage:
    if result.exception:
        print(result.output)
        raise result.exception
    assert not result.exception


def test_invalid_color(config, runner):
    config.write('color = 12\npath = "/"\n')
    result = runner.invoke(cli, ["list"])
    assert result.exception
    assert (
        "Error: Bad color setting. Invalid type (expected str, got int)."
        in result.output
    )


def test_invalid_color_arg(config, runner):
    config.write('path = "/"\n')
    result = runner.invoke(cli, ["--color", "12", "list"])
    assert result.exception
    assert "Usage:" in result.output


def test_missing_path(config, runner):
    config.write('color = "auto"\n')
    result = runner.invoke(cli, ["list"])
    assert result.exception
    assert "Error: Missing 'path' setting." in result.output


@pytest.mark.xfail(reason="Not implemented")
def test_extra_entry(config, runner):
    config.write("color = auto\ndate_format = %Y-%m-%d\npath = /\nblah = false\n")
    result = runner.invoke(cli, ["list"])
    assert result.exception
    assert "Error: Invalid configuration entry" in result.output


@pytest.mark.xfail(reason="Not implemented")
def test_extra_section(config, runner):
    config.write("date_format = %Y-%m-%d\npath = /\n[extra]\ncolor = auto\n")
    result = runner.invoke(cli, ["list"])
    assert result.exception
    assert "Invalid configuration section" in result.output


def test_missing_cache_dir(config, runner, tmpdir):
    cache_dir = tmpdir.join("does").join("not").join("exist")
    cache_file = cache_dir.join("cache.sqlite")

    config.write(f'path = "{tmpdir}/*"\ncache_path = "{cache_file}"\n')

    result = runner.invoke(cli)
    assert not result.exception
    assert cache_dir.isdir()
    assert cache_file.isfile()


def test_date_field_in_time_format(config, runner, tmpdir):
    config.write('path = "/"\ntime_format = "%Y-%m-%d"\n')
    result = runner.invoke(cli)
    assert result.exception
    assert (
        "Found date component in `time_format`, please use `date_format` for that."
        in result.output
    )


def test_date_field_in_time(config, runner, tmpdir):
    config.write('path = "/"\ndate_format = "%Y-%d-:%M"\n')
    result = runner.invoke(cli)
    assert result.exception
    assert (
        "Found time component in `date_format`, please use `time_format` for that."
        in result.output
    )


def test_colour_validation_auto(config):
    with patch(
        "todoman.configuration.find_config",
        return_value=(str(config)),
    ):
        cfg = load_config()

    assert cfg["color"] == "auto"


def test_colour_validation_always(config):
    config.write("color = 'always'\n", "a")
    with patch(
        "todoman.configuration.find_config",
        return_value=(str(config)),
    ):
        cfg = load_config()

    assert cfg["color"] == "always"


def test_colour_validation_invalid(config):
    config.write("color = 'on_weekends_only'\n", "a")
    with patch(
        "todoman.configuration.find_config",
        return_value=(str(config)),
    ), pytest.raises(ConfigurationError):
        load_config()
