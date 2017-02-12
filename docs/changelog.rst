Changelog
=========

This file contains a brief summary of new features and dependency changes or
releases, in reverse chronological order.

v2.0.3
------

* Fix crash if the cache directory does not exist (attempt to create it first).

v2.0.2
------

* Fix a crash after editing or completing a todo.

v2.0.1
------

* Fix a packaging error.

v2.0.0
------

New features
~~~~~~~~~~~~
* New flag ``--porcelain`` for programmatic integrations to use. See the
  ``integrations`` section :doc:`here </usage>` for details.
* Implement a new :doc:`configuration option </configure>`: ``default_due``.
* The configuration file is now pre-emptively validated. Users will be warned
  of any inconsistencies.
* The ``list`` command has a new ``--due`` flag to filter tasks due soon.
* Todo ids are now persisted in a cache. They can be manually purged using
  ``flush``.

Packaging changes
~~~~~~~~~~~~~~~~~
* New runtime dependency: configobj
* New runtime dependency: python-dateutil
* New test dependency: flake8-import-order.
