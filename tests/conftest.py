import os
from datetime import datetime
from uuid import uuid4

import pytest
import pytz
from click.testing import CliRunner
from dateutil.tz import tzlocal
from hypothesis import HealthCheck, settings, Verbosity

from todoman import model
from todoman.formatters import DefaultFormatter, HumanizedFormatter


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


@pytest.fixture
def now_for_tz():

    def inner(tz='CET'):
        """
        Provides the current time cast to a given timezone.

        This helper should be used in place of datetime.now() when the date
        will be compared to some pre-computed value that assumes a determined
        timezone.
        """
        return datetime.now().replace(tzinfo=tzlocal()) \
            .astimezone(pytz.timezone(tz))

    return inner


@pytest.fixture
def todo_factory(default_database):
    def inner(**attributes):
        todo = model.Todo(new=True)
        todo.list = list(default_database.lists())[0]

        attributes.setdefault('summary', 'YARR!')
        for name, value in attributes.items():
            setattr(todo, name, value)

        default_database.save(todo)

        return todo

    return inner


@pytest.fixture
def default_formatter():
    formatter = DefaultFormatter(tz_override=pytz.timezone('CET'))
    return formatter


@pytest.fixture
def humanized_formatter():
    formatter = HumanizedFormatter(tz_override=pytz.timezone('CET'))
    return formatter


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
