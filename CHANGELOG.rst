Changelog
=========

This file contains a brief summary of new features and dependency changes or
releases, in reverse chronological order.

v4.2.0
------

* Added full support for categories.

v4.1.0
------

* The "table" layout has been dropped in favour of a simpler, fluid layout. As
  such, ``tabulate`` is not longer a required dependency.
* Added support for python 3.10.

v4.0.1
------

* Fix issue passing arguments to ``default_command``.
* Various documentation improvements.

v4.0.0
------

Breaking changes in the configuration format
********************************************

The configuration format is changing with release 4.0.0. We currently depend on
an unmaintained library for configuration. It's not currently in a working
state, and while some distributions are patching it, setting up a clean
environment is a bit non-trivial, and the situation will only degrade in future.

The changes in format are be subtle, and also come with an intention to add
further extensibility in future. Configuration files will be plain python. If
you don't know Python don't worry, you don't _need_ to know Python.

I'll take my own config as a reference. The pre-4.0.0 format is:

```dosini
[main]
path = ~/.local/share/calendars/*
time_format = '%H:%M'
default_list = todo
humanize = true
startable = true
```

The 4.0.0 version would look like this:

```python
path = "~/.local/share/calendars/*"
time_format = "%H:%M"
default_list = "todo"
humanize = True
startable = True
```

Key differences:

- The `[main]` header is no longer needed.
- All strings must be quoted (this was previously optional).
- True and False start with uppercase.
- Using `yes` or `on` is no longer valid; only `True` and `False` are valid.

That's basically it. This lets up drop the problematic dependency, and we don't
actually need anything to read the config: it's just python code like the rest
of `todoman`!

For those users who _are_ python developers, you'll note this gives some
interesting flexibility: you CAN add any custom python code into the config
file. For example, you can defined the `path` programatically:

.. code-block:: python

    def get_path() -> str:
        ...

    path = get_path

Dropped support
***************

* Dropped support older Python versions. Only 3.8 and 3.9 are now supported.

Minor changes
*************

* Added support for python 3.9.
* The dependency `configobj` is no longer required.
* Click 8.0 is now supported.
* Fix crash when ``default_command`` has arguments.

v3.9.0
------

* The man page has been improved. ``sphinx-click`` is now required to build the
  documentation.

v3.8.0
------
* Don't display list if there's only one list (of one list has been specified).
* Fixed several issues when using dates with no times.
* Dropped support for Python 3.4.

v3.7.0
------
* Properly support iCal files with dates (instead of datetimes).

v3.6.0
------
* Allow passing a custom configuration file with the ``--config/-c`` option.
* Cached list metadata is now invalidated when it has changed on-disk.
* Support for click < 6.0 has been dropped (it wasn't actually working
  perfectly any more anyway). Click 7.x is the only currently supported
  version.
* ``click-repl`` is now listed as an optional dependency. It is required for
  the ``todo repl`` command.
* Add the ``default_priority`` config setting.
* Drop support for Python 3.4.

v3.5.0
------
* Fix crashes due to API changes in icalendar 4.0.3.
* Dropped compatibility for icalendar < 4.0.3.

v3.4.1
------
* Support Python 3.7.
* Support click>=7.0.
* Properly parse RBGA colours.

v3.4.0
------

* Add ``-r`` option to ``new`` to read description from ``stdin``.
* Add a dedicated zsh completion function.
* Lists matching is now case insensitive, unless there are multiple lists with
  colliding names, in which case those will be treated case-sensitive.
* Fix some tests that failed due to test dependency changes.

v3.3.0
------

* New runtime dependency: ``click-log``.
* Drop support for Python 3.3, which has reached its end of life cycle.
* Add `--raw` flag to `edit`. This allows editing the raw icalendar file, but
  **only use this if you really know what you're doing**. There's a big risk of
  data loss, and this is considered a developer / expert feature!

v3.2.4
------

* Deploy new versions to PyPI using ``twine``. Travis doesn't seem to be
  working.

v3.2.3
------

* Tests should no longer fail with ``pyicu`` installed.
* Improved documentation regarding how to test locally.

v3.2.2
------

* Initial support for (bash) autocompletion.
* The location field is not printed as part of ``--porcelain``.

v3.2.1
------

* Fix start-up crash caused by click_log interface change.
* Dropped runtime dependency: ``click_log``.

v3.2.0
------

* Completing recurring todos now works as expected and does not make if
  disappear forever.

v3.1.0
------

* Last-modified fields of todos are now updated upon edition.
* Sequence numbers are now properly increased upon edition.
* Add new command ``todo cancel`` to cancel an existing todo without deleting
  it.
* Add a new setting ``default_command``.
* Replace ``--all`` and ``--done-only`` with  ``--status``, which allows
  fine-grained status filtering. Use ``--status ANY`` or ``--status COMPLETED``
  to obtain the same results as the previous flags.
* Rename ``--today`` flag to ``--startable``.
* Illegal start dates (eg: start dates that are not before the due date) are
  ignored and are removed when saving an edited todo.

v3.0.1
------

* Fix a crash for users upgrading from pre-v3.0.0, caused due to the cache's
  schema not being updated.

v3.0.0
------

New features
************

* Add a ``today`` setting and flag to exclude todos that start in the future.
* Add the ``--humanize`` to show friendlier date times (eg: ``in 3 hours``).
* Drop ``--urgent`` and introduced ``--priority``, which allows fine-filtering
  by priority.
* Add support for times in due dates, new ``time_format`` setting.
* Use the system's date format as a default.
* Add list selector to the interactive editor.
* Add ``--start=[before|after] [DATE]`` option for ``list`` to only show
  todos starting before/after given date.
* Add flag "--done-only" to todo list. Displays only completed tasks.
* Make the output of move, delete, copy and flush consistent.
* Porcelain now outputs proper JSON, rather than one-JSON-per-line.
* Increment sequence number upon edits.
* Print a descriptive message when no lists are found.
* Add full support for locations.

Packaging changes
*****************

* New runtime dependency: ``tabulate``.
* New runtime dependency: ``humanize``.
* New supported python version: ``pypy3``.
* Include an alternative [much faster] entry point (aka "bin") which we
  recommend all downstream packagers use. Please see the :ref:`Notes for
  Packagers <notes-for-packagers>` documentation for further details.

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
