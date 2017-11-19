__all__ = [
    'pyicu_sensitive',
]

import pytest


def is_pyicu_installed():
    try:
        import icu  # noqa: F401: This is an import to tests if it's installed.
    except ImportError:
        return False
    else:
        return True


pyicu_sensitive = pytest.mark.skipif(
    is_pyicu_installed(),
    reason="This test cannot be run with pyicu installed.",
)
