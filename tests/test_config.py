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
    # Redefining XDG_CONFIG_HOME does not work here, because the xdg module
    # saves the directory locations at startup time.
    # You MUST set XDG_CONFIG_HOME to a nonexistant directory (or one without a
    # settings files) before running tests, or this one will fail.
    result = CliRunner().invoke(
        cli,
        catch_exceptions=True,
    )
    assert result.exception
    assert "No configuration file found" in result.output
