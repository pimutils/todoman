from __future__ import annotations

import os
import sys
from subprocess import PIPE
from subprocess import Popen

import py
from click.testing import CliRunner

from todoman.cli import cli


def test_main(tmpdir: py.path.local, runner: CliRunner) -> None:
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    env = os.environ.copy()
    env["PYTHONPATH"] = root

    cli_result = runner.invoke(cli, ["--version"])

    pipe = Popen(
        [sys.executable, "-m", "todoman", "--version"],
        stdout=PIPE,
        env=env,
    )
    main_output = pipe.communicate()[0]

    assert cli_result.output == main_output.decode()
