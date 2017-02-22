Changelog
=========

This file contains a brief summary of new features and dependency changes or
releases, in reverse chronological order.

v2.2.0
------

* Basic support for times in due dates, new ``time_format`` configuration
  parameter.
* Use the system's date format as a default.
* Show "Today" or "Tomorrow" when due date is today/tomorrow respectively.

v2.1.0
------

* The global ``--verbosity`` option has been introduced. It doesn't do much for
  now though, because we do not have many debug logging statements.
* New PyPI dependency ``click-log``.
* The ``--no-human-time`` flag is gone. Integrations/scripts might want to look
  at ``--porcelain`` as an alternative.
* Fix crash when running ``todo new``.
* Fixes some issues when filtering todos from different timezones.
* Attempt to create the cache file's directory if it does not exist.
* Fix crash when running ``--porcelain show``.
* Show ``id`` for todos everywhere (eg: including new, etc).
* Add the ``ctrl-s`` shortcut for saving in the interactive editor.

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
