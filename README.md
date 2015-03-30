Todoman
=======

Todoman is a simple, standards-based,
[cli](https://en.wikipedia.org/wiki/Command-line_interface) todo (aka: task)
manager. Todos are stored into [ical](https://tools.ietf.org/html/rfc5545)
files, which means you can sync them via
[CalDav](http://en.wikipedia.org/wiki/CalDAV) using, for example,
[vdirsyncer](https://github.com/untitaker/vdirsyncer).

Features
--------

 * Listing, editing and creating todos.
 * Todos are read from individual ics files from the configured directory.
 * There's support for the most common TODO features for now (summary,
   description, location, due date and priority) for now.
 * Todoman should run on any major operating system.
 * Unsupported fields may not be shown but are *never* deleted or altered.

Caveats
-------

Priority granularity hasn't been completely implemented yet. icalendar
supports priorities 1-9 or none. Todoman supports only none or 1 (highest).

Due dates are generally shown and editable as dates with no time component.

Support for the `percent-completed` attribute is incomplete. Todoman can only
mark todos as completed (100%), and will nor reflect nor allow editing for
values for `percent > 0 ^ percent < 100`.

Requirements
------------

 * python
 * docopt
 * icalendar
 * urwid
 * pyxdg

Installation
------------

If todoman is not in your distribution's repositories, to install it run
`python setup.py install`. 

Usage
-----

You'll need to configure Todoman first. Required values are a path where your
todos are stored and the date format you prefer. Check the
`todoman.conf.sample` file, which should serve as a reference.  
The configuration file should be placed in
`$XDG_CONFIG_DIR/todoman/todoman.conf`. `$XDG_CONFIG_DIR` will be `~/.config`
is most situations.

Usage is rater simple:

    todo
    todo new
    todo edit ID
    todo show ID
    todo help | -h | --help
    todo --version

When no arguments are passed, Todoman will list all todos, along with their
IDs. IDs are not immutable, and will change as you add/delete new entries.

Sample output:

    Output sample:
    [ ] ! 2015-04-30 Close bank account (0%)
    [ ] !            Send minipimer back for warranty replacement (0%)
    [X]   2015-03-29 Buy soy milk (100%)
    [ ]              Fix the iPad's screen (0%)
    [ ]              Fix the Touchad battery (0%)

If you want to synchronize your todos, you'll needs something that syncs via
CalDav. [vdirsyncer](https://github.com/untitaker/vdirsyncer) is the recomended
tool for this.

LICENCE
-------

Todoman is licensed under the MIT licence. See LICENCE for details.
