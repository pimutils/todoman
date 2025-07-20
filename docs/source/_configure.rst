Configuring
===========

You'll need to configure Todoman before the first usage, using its simple
ini-like configuration file.

Configuration File
------------------

The configuration file should be placed in
``$XDG_CONFIG_HOME/todoman/config.py``. ``$XDG_CONFIG_HOME`` defaults to
``~/.config`` is most situations, so this will generally be
``~/.config/todoman/config.py``.

.. include:: confspec.tmp

Sample configuration
--------------------

The below example should serve as a reference. It will read ics files from any
directory inside ``~/.local/share/calendars/``, uses the ISO-8601 date format,
and set the due date for new todos in 48hs.

.. literalinclude:: ../../config.py.sample
  :language: python

Color and displayname
---------------------

- You can set a color for each task list by creating a ``color`` file containing
  a color code in the hex format: ``#RRGGBB``.
- A file named ``displayname`` indicates how the task list should be named and
  is needed when there are multiple directories sharing a name, e.g.: when using
  multiple $CloudInstances. The default is the directory name.

See also `relevant documentation for the vdir format
<https://vdirsyncer.pimutils.org/en/stable/vdir.html#metadata>`_.

Timezone
--------

Todoman will use the system-wide configured timezone. If this doesn't work for
you, you _may_ override the timezone by specifying the ``TZ`` environment
variable.

For instruction on changing your system's timezone, consult your distribution's
documentation.
