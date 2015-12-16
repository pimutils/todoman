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
