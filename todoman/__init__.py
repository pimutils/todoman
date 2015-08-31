from setuptools_scm import get_version
import pkg_resources

try:
    __version__ = get_version(version_scheme='post-release')
except LookupError:
    __version__ = pkg_resources.get_distribution('todoman').version
