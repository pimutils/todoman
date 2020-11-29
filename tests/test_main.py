import os
import sys
from subprocess import PIPE
from subprocess import Popen

from todoman.cli import cli


def test_main(tmpdir, runner):
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
