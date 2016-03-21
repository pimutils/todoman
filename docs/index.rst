Todoman
=======

Todoman is a simple, standards-based, cli todo (aka: task) manager. Todos
are stored into icalendar_ files, which means you can sync them via CalDAV_
using, for example, vdirsyncer_.

Todoman is now part of the ``pimutils`` project, and is hosted at GitHub_. The
original location at GitLab.com_ is still kept as a mirror.


.. _icalendar: https://tools.ietf.org/html/rfc5545
.. _CalDav: http://en.wikipedia.org/wiki/CalDAV
.. _vdirsyncer: https://vdirsyncer.readthedocs.org/
.. _GitHub: https://github.com/pimutils/todoman
.. _GitLab.com: https://gitlab.com/hobarrera/todoman/

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

Planned Features
----------------

* Keep a SQL cache of all the entries, and update this only when the
  modification time of the ics files changes. This design is inspired
  (identical, really) to what khal does.
* Interactive mode. Including a list of todos, and easy selection for marking
  done and editing.
* Support for other icalendar fields which are not implemented yet.
* Customizable output format.

Pull requests and patches are welcome! 😉 Please report any issues on the
project `issue tracker <https://gitlab.com/hobarrera/todoman/issues>`_.

Caveats
-------

Priority granularity hasn't been completely implemented yet. Icalendar
supports priorities 1-9 or none. Todoman supports only none or 1 (highest).

Due dates are generally shown and editable as dates with no time component.

Support for the ``percent-completed`` attribute is incomplete. Todoman can only
mark todos as completed (100%), and will nor reflect nor allow editing for
values for ``percent > 0 ^ percent < 100``.

Table of Contents
=================

.. toctree::
   :maxdepth: 2

   install
   configure
   usage
   licence

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

