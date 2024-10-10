Todoman
=======

`CI status <https://builds.sr.ht/~whynothugo/todoman/commits/main>`_
| `Coverage <https://codecov.io/gh/pimutils/todoman>`_
| `Documentation <https://todoman.rtfd.org/>`_
| `ISC Licence <https://github.com/pimutils/todoman/blob/main/LICENCE>`_

Todoman is a simple, standards-based, cli todo (aka: task) manager. Todos
are stored into `icalendar <https://tools.ietf.org/html/rfc5545>`_ files, which
means you can sync them via `CalDAV <http://en.wikipedia.org/wiki/CalDAV>`_
using, for example, `vdirsyncer <https://vdirsyncer.readthedocs.org/>`_.

Todoman is now part of the ``pimutils`` project, and is hosted at `GitHub
<https://github.com/pimutils/todoman>`_.

Todoman should run fine on any Unix-like OS. It's been tested on GNU/Linux,
BSD, and macOS.  We do not support windows, and very basic testing seems to
indicate it does not work.

Feel free to join the IRC channel: #pimutils on irc.libera.chat.

Features
--------

* Listing, editing and creating todos.
* Todos are read from individual ics files from the configured directory. This
  matches the `vdir <https://vdirsyncer.readthedocs.org/en/latest/vdir.html>`_
  specification.
* There's support for the most common TODO features for now (summary,
  description, location, due date and priority).
* Todoman should run on any major operating system (except Windows).
* Unsupported fields may not be shown but are *never* deleted or altered.

Documentation
-------------

For detailed usage, configuration and contributing documentation, please
consult the latest version of the manual at readthedocs_.

.. _readthedocs: https://todoman.readthedocs.org/

LICENCE
-------

Todoman is licensed under the ISC licence. See LICENCE for details.
