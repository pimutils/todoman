from click.testing import CliRunner

import pytest


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
