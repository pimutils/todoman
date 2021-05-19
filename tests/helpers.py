__all__ = [
    "pyicu_sensitive",
]

import os
from tempfile import TemporaryDirectory

import pytest


def is_fs_case_sensitive():
    with TemporaryDirectory() as tmpdir:
        os.mkdir(os.path.join(tmpdir, "casesensitivetest"))
        try:
            os.mkdir(os.path.join(tmpdir, "casesensitiveTEST"))
            return True
        except FileExistsError:
            return False


def is_pyicu_installed():
    try:
        import icu  # noqa: F401: This is an import to tests if it's installed.
    except ImportError:
        return False
    else:
        return True


fs_case_sensitive = pytest.mark.skipif(
    not is_fs_case_sensitive(),
    reason="This test cannot be run when the fs is not case sensitive.",
)


pyicu_sensitive = pytest.mark.skipif(
    is_pyicu_installed(),
    reason="This test cannot be run with pyicu installed.",
)
