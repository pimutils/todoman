import os

import pytest
from click.testing import CliRunner
from hypothesis import HealthCheck, Verbosity, settings


@pytest.fixture
def config(tmpdir):
    path = tmpdir.join('config')
    tmpdir.mkdir('default')  # default calendar
    path.write('[main]\n'
               'path = {}/*\n'
               'date_format = %Y-%m-%d\n'
               .format(str(tmpdir)))
    return path


@pytest.fixture
def runner(config):
    return CliRunner(env={
        'TODOMAN_CONFIG': str(config)
    })


@pytest.fixture
def create(tmpdir):
    def inner(name, content):
        tmpdir.join('default').join(name).write(
            'BEGIN:VCALENDAR\n'
            'BEGIN:VTODO\n' +
            content +
            'END:VTODO\n'
            'END:VCALENDAR'
        )

    return inner


settings.register_profile("ci", settings(
    max_examples=1000,
    verbosity=Verbosity.verbose,
    suppress_health_check=[HealthCheck.too_slow]
))
settings.register_profile("deterministic", settings(
    derandomize=True,
))

if os.getenv('DETERMINISTIC_TESTS', 'false').lower() == 'true':
    settings.load_profile("deterministic")
elif os.getenv('CI', 'false').lower() == 'true':
    settings.load_profile("ci")
