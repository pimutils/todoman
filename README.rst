Todoman
=======

Todoman is a simple, standards-based, cli todo (aka: task) manager. Todos
are stored into `icalendar <https://tools.ietf.org/html/rfc5545>`_ files, which
means you can sync them via `CalDAV <http://en.wikipedia.org/wiki/CalDAV>`_
using, for example, `vdirsyncer <https://vdirsyncer.readthedocs.org/>`_.

Official website and repository is hosted at `GitLab.com
<https://gitlab.com/hobarrera/todoman>`_.

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

Requirements
------------

Running ``setup.py`` (as described below, in Installation) should install all
necessary dependencies via pip. The only pre-requisite for this is python 3,
which ships with most modern distributions.

All python dependencies are listed under ``requirements.txt``.

Todoman will not work with python 2. However, keep in mind that python 2 and
python 3 can coexist (and most distributions actually ship both).

Installation
------------

If todoman is not in your distribution's repositories, to install it run::

    pip install todoman

If pip is not available either (this is most unlikely), you'll need to download
the source tarball and run::

    python3 setup.py install

Usage
-----

You'll need to configure Todoman first. Required values are a path where your
todos are stored and the date format you prefer. Check the
``todoman.conf.sample`` file, which should serve as a reference.  
The configuration file should be placed in
``$XDG_CONFIG_DIR/todoman/todoman.conf``. ``$XDG_CONFIG_DIR`` defaults to
``~/.config`` is most situations.

Usage is rather simple::

    todo
    todo new
    todo edit ID
    todo show ID
    todo help | -h | --help
    todo --version

When no arguments are passed, Todoman will list all todos, along with their
IDs. IDs are not immutable, and will change as you add/delete new entries.

Sample output::

    [ ] ! 2015-04-30 Close bank account (0%)
    [ ] !            Send minipimer back for warranty replacement (0%)
    [X]   2015-03-29 Buy soy milk (100%)
    [ ]              Fix the iPad's screen (0%)
    [ ]              Fix the Touchad battery (0%)

If you want to synchronize your todos, you'll needs something that syncs via
CalDAV. `vdirsyncer`_ is the
recommended tool for this.

Color and displayname
---------------------

- You can set a color for each task list by creating a ``color`` file containing
  a colorcode in the format ``#RRGGBB``.
- A file named ``displayname`` decides how the task list should be named. The
  default is the directory name.

See also `this discussion about metadata for collections in
vdirsyncer <https://github.com/untitaker/vdirsyncer/issues/125>`_.

Interactive shell
-----------------

If you install `click-repl <https://github.com/untitaker/click-repl>`_, todoman
gets a new command called ``repl``, which lauches an interactive shell with
tab-completion.

LICENCE
-------

Todoman is licensed under the MIT licence. See LICENCE for details.
