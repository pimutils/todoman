Configuring
===========

You'll need to configure Todoman before the first usage, using its simple
ini-like configuration file.

Configuration File
------------------

The configuration file should be placed in
``$XDG_CONFIG_DIR/todoman/todoman.conf``. ``$XDG_CONFIG_DIR`` defaults to
``~/.config`` is most situations, so this will generally be
``~/.config/todoman/todoman.conf``.

Main section
~~~~~~~~~~~~

 * ``path``: The path to where your todos are located. It can also be a glob
   expresion if you wish to include mutiple directories.
 * ``date_format``: The date format used both for displaying dates, and parsing
   input dates.
   If this option is not specified the ISO-8601 (``%Y-%m-%d``) format is used.

Sample configuration
--------------------

The below example should serve as a reference. It will read ics files from any
directory inside ``~/.local/share/calendars/``, and use the ISO-8601 date
format (note that this is the default format, so this particular declaration is
redundant).

.. literalinclude:: ../todoman.conf.sample
  :language: ini

Color and displayname
---------------------

- You can set a color for each task list by creating a ``color`` file containing
  a colorcode in the format ``#RRGGBB``.
- A file named ``displayname`` decides how the task list should be named. The
  default is the directory name.

See also `this discussion about metadata for collections in
vdirsyncer <https://github.com/untitaker/vdirsyncer/issues/125>`_.
