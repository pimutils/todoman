Man page
========

.. click:: todoman.cli:cli
   :prog: todo
   :show-nested:

Description
-----------

Todoman is a simple, standards-based, cli todo (aka: task) manager. Todos are
stored into *icalendar* files, which means you can sync them via *CalDAV*
using, for example, *vdirsyncer*.

Usage
-----

.. include:: usage.rst

Configuring
-----------

.. include:: configure.rst

Caveats
-------

Support for the ``percent-completed`` attribute is incomplete. Todoman can only
mark todos as completed (100%), and will not reflect nor allow editing for
values for ``percent > 0 ^ percent < 100``.

Contributing
------------

For information on contributing, see:
https://todoman.readthedocs.io/en/stable/contributing.html

LICENCE
-------

Todoman is licensed under the ISC licence. See LICENCE for details.
