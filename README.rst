Todoman
=======

.. image:: https://ci.gitlab.com/projects/7057/status.png?ref=master
  :target: https://ci.gitlab.com/projects/7057?ref=master
  :alt: build status

.. image:: https://readthedocs.org/projects/todoman/badge/
  :target: https://todoman.rtfd.org/
  :alt: documentation

.. image:: https://img.shields.io/pypi/v/todoman.svg
  :target: https://pypi.python.org/pypi/todoman
  :alt: version on pypi

.. image:: https://img.shields.io/pypi/l/todoman.svg
  :alt: licence

Todoman is a simple, standards-based, cli todo (aka: task) manager. Todos
are stored into `icalendar <https://tools.ietf.org/html/rfc5545>`_ files, which
means you can sync them via `CalDAV <http://en.wikipedia.org/wiki/CalDAV>`_
using, for example, `vdirsyncer <https://vdirsyncer.readthedocs.org/>`_.

Official website and repository is hosted at `GitLab.com
<https://gitlab.com/hobarrera/todoman>`_.

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

For detailed configuration, have a look at the latest docs at readthedocs_.

.. _readthedocs: https://todoman.rtfd.org/

LICENCE
-------

Todoman is licensed under the MIT licence. See LICENCE for details.
