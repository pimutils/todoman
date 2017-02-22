Todoman
=======

.. image:: https://travis-ci.org/pimutils/todoman.svg?branch=master
  :target: https://travis-ci.org/pimutils/todoman
  :alt: Travis CI build status

.. image:: https://codecov.io/gh/pimutils/todoman/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/pimutils/todoman
  :alt: Codecov coverage report

.. image:: https://readthedocs.org/projects/todoman/badge/
  :target: https://todoman.rtfd.org/
  :alt: documentation

.. image:: https://img.shields.io/pypi/v/todoman.svg
  :target: https://pypi.python.org/pypi/todoman
  :alt: version on pypi

.. image:: https://img.shields.io/pypi/l/todoman.svg
  :target: https://github.com/pimutils/todoman/blob/master/LICENCE
  :alt: licence

.. image:: https://img.shields.io/badge/Say%20Thanks!-%F0%9F%A6%89-1EAEDB.svg
  :target: https://saythanks.io/to/hobarrera
  :alt: Say Thanks!

Todoman is a simple, standards-based, cli todo (aka: task) manager. Todos
are stored into `icalendar <https://tools.ietf.org/html/rfc5545>`_ files, which
means you can sync them via `CalDAV <http://en.wikipedia.org/wiki/CalDAV>`_
using, for example, `vdirsyncer <https://vdirsyncer.readthedocs.org/>`_.

Todoman is now part of the ``pimutils`` project, and is hosted at `GitHub
<https://github.com/pimutils/todoman>`_. The original location at `GitLab.com
<https://gitlab.com/hobarrera/todoman>`_ is still kept as a mirror.

Features
--------

* Listing, editing and creating todos.
* Todos are read from individual ics files from the configured directory. This
  matches the `vdir <https://vdirsyncer.readthedocs.org/en/latest/vdir.html>`_
  specification.
* There's support for the most common TODO features for now (summary,
  description, location, due date and priority) for now.
* Todoman should run on any major operating system.
* Unsupported fields may not be shown but are *never* deleted or altered.

Documentation
-------------

For detailed usage, configuration and contributing documentation, please
consult the latest version of the manual at readthedocs_.

.. _readthedocs: https://todoman.readthedocs.org/

LICENCE
-------

Todoman is licensed under the MIT licence. See LICENCE for details.
