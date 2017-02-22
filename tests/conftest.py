import os
from uuid import uuid4

import pytest
from click.testing import CliRunner
from hypothesis import HealthCheck, settings, Verbosity

from todoman import model


@pytest.fixture
def default_database(tmpdir):
    return model.Database(
        [tmpdir.mkdir('default')],
        tmpdir.mkdir(uuid4().hex).join('cache.sqlite3'),
    )


@pytest.fixture
def config(tmpdir, default_database):
    path = tmpdir.join('config')
    path.write('[main]\n'
               'path = {}/*\n'
               'date_format = %Y-%m-%d\n'
               'time_format = \n'
               'cache_path = {}\n'
               .format(str(tmpdir), str(tmpdir.join('cache.sqlite3'))))
    return path


@pytest.fixture
def runner(config):
    return CliRunner(env={
        'TODOMAN_CONFIG': str(config)
    })


@pytest.fixture
def create(tmpdir):
    def inner(name, content, list_name='default'):
        tmpdir.ensure_dir(list_name).join(name).write(
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
