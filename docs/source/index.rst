Todoman
=======

Todoman is a simple, standards-based, cli todo (aka: task) manager. Todos
are stored into icalendar_ files, which means you can sync them via CalDAV_
using, for example, vdirsyncer_.

Todoman is now part of the ``pimutils`` project, and is hosted at GitHub_.

.. _icalendar: https://tools.ietf.org/html/rfc5545
.. _CalDav: http://en.wikipedia.org/wiki/CalDAV
.. _vdirsyncer: https://vdirsyncer.readthedocs.org/
.. _GitHub: https://github.com/pimutils/todoman

Features
--------

* Listing, editing and creating todos.
* Todos are read from individual ics files from the configured directory. This
  matches the `vdir <https://vdirsyncer.readthedocs.org/en/latest/vdir.html>`_
  specification.
* There's support for the most common TODO features for now (summary,
  description, location, due date and priority).
* Runs on any Unix-like OS. It's been tested on GNU/Linux, BSD and macOS.
* Unsupported fields may not be shown but are *never* deleted or altered.

Contributing
------------

See :doc:`contributing` for details on contributing.

Caveats
-------

Support for the ``percent-completed`` attribute is incomplete. Todoman can only
mark todos as completed (100%), and will not reflect nor allow editing for
values for ``percent > 0 ^ percent < 100``.

Table of Contents
=================

.. toctree::
   :maxdepth: 2

   install
   configure
   usage
   man
   contributing
   changelog
   licence

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
