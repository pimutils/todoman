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
