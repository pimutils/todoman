Configuring
===========

You'll need to configure Todoman before the first usage. Required values are a
path where your todos are stored and the date format you prefer.


The configuration file should be placed in
``$XDG_CONFIG_DIR/todoman/todoman.conf``. ``$XDG_CONFIG_DIR`` defaults to
``~/.config`` is most situations.

The below example should serve as a reference.

Sample configuration
--------------------

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
