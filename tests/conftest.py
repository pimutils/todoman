import os
import time
from datetime import datetime
from uuid import uuid4

import pytest
import pytz
from click.testing import CliRunner
from dateutil.tz import tzlocal
from hypothesis import HealthCheck
from hypothesis import Verbosity
from hypothesis import settings

from todoman import model
from todoman.formatters import DefaultFormatter
from todoman.formatters import HumanizedFormatter


@pytest.fixture()
def default_database(tmpdir):
    return model.Database(
        [tmpdir.mkdir("default")],
        tmpdir.mkdir(uuid4().hex).join("cache.sqlite3"),
    )


@pytest.fixture()
def config(tmpdir, default_database):
    config_path = tmpdir.join("config.py")
    config_path.write(
        f'path = "{tmpdir}/*"\n'
        'date_format = "%Y-%m-%d"\n'
        'time_format = ""\n'
        f'cache_path = "{str(tmpdir.join("cache.sqlite3"))}"\n'
    )
    return config_path


@pytest.fixture()
def runner(config, sleep):
    class SleepyCliRunner(CliRunner):
        """
        Sleeps before invoking to make sure cache entries have expired.
        """

        def invoke(self, *args, **kwargs):
            sleep()
            return super().invoke(*args, **kwargs)

    return SleepyCliRunner(env={"TODOMAN_CONFIG": str(config)})


@pytest.fixture()
def create(tmpdir):
    def inner(name, content, list_name="default"):
        path = tmpdir.ensure_dir(list_name).join(name)
        path.write(
            "BEGIN:VCALENDAR\nBEGIN:VTODO\n" + content + "END:VTODO\nEND:VCALENDAR"
        )
        return path

    return inner


@pytest.fixture()
def now_for_tz():
    def inner(tz="CET"):
        """
        Provides the current time cast to a given timezone.

        This helper should be used in place of datetime.now() when the date
        will be compared to some pre-computed value that assumes a determined
        timezone.
        """
        return datetime.now().replace(tzinfo=tzlocal()).astimezone(pytz.timezone(tz))

    return inner


@pytest.fixture()
def todo_factory(default_database):
    def inner(**attributes):
        todo = model.Todo(new=True)
        todo.list = list(default_database.lists())[0]

        attributes.setdefault("summary", "YARR!")
        for name, value in attributes.items():
            setattr(todo, name, value)

        default_database.save(todo)

        return todo

    return inner


@pytest.fixture()
def default_formatter():
    formatter = DefaultFormatter(tz_override=pytz.timezone("CET"))
    return formatter


@pytest.fixture()
def humanized_formatter():
    formatter = HumanizedFormatter(tz_override=pytz.timezone("CET"))
    return formatter


@pytest.fixture(scope="session")
def sleep(tmpdir_factory):
    """
    Sleeps as long as needed for the filesystem's mtime to pick up differences

    Measures how long we need to sleep for the filesystem's mtime precision to
    pick up differences and returns a function that sleeps that amount of time.

    This keeps test fast on systems with high precisions, but makes them pass
    on those that don't (I'm looking at you, macOS).
    """
    tmpfile = tmpdir_factory.mktemp("sleep").join("touch_me")

    def touch_and_mtime():
        tmpfile.open("w").close()
        stat = os.stat(str(tmpfile))
        return getattr(stat, "st_mtime_ns", stat.st_mtime)

    def inner():
        time.sleep(i)

    i = 0.00001
    while i < 100:
        # Measure three times to avoid things like 12::18:11.9994 [mis]passing
        first = touch_and_mtime()
        time.sleep(i)
        second = touch_and_mtime()
        time.sleep(i)
        third = touch_and_mtime()

        if first != second != third:
            i *= 1.1
            return inner
        i = i * 10

    # This should never happen, but oh, well:
    raise Exception(
        "Filesystem does not seem to save modified times of files. \n"
        "Cannot run tests that depend on this."
    )


@pytest.fixture()
def todos(default_database, sleep):
    def inner(**filters):
        sleep()
        default_database.update_cache()
        return default_database.todos(**filters)

    return inner


settings.register_profile(
    "ci",
    settings(
        deadline=None,
        max_examples=1000,
        verbosity=Verbosity.verbose,
        suppress_health_check=[HealthCheck.too_slow],
    ),
)
settings.register_profile(
    "deterministic",
    settings(
        derandomize=True,
    ),
)

if os.getenv("DETERMINISTIC_TESTS", "false").lower() == "true":
    settings.load_profile("deterministic")
elif os.getenv("CI", "false").lower() == "true":
    settings.load_profile("ci")
