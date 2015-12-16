Usage
=====

Usage is rather simple::

    Usage: todo [OPTIONS] COMMAND [ARGS]...

    Options:
      --human-time / --no-human-time  Accept informal descriptions such as
                                      "tomorrow" instead of a properly formatted
                                      date.
      --version                       Show the version and exit.
      --help                          Show this message and exit.

    Commands:
      done   Mark a task as done.
      edit   Edit a task interactively.
      flush  Delete done tasks.
      list   List unfinished tasks.
      new    Create a new task with SUMMARY.
      repl   Start an interactive shell.
      show   Show details about a task.

When no arguments are passed, Todoman will list all todos, along with their
IDs. IDs are not immutable, and will change as you add/delete new entries.  

Sample output::

    [ ] ! 2015-04-30 Close bank account (0%)
    [ ] !            Send minipimer back for warranty replacement (0%)
    [X]   2015-03-29 Buy soy milk (100%)
    [ ]              Fix the iPad's screen (0%)
    [ ]              Fix the Touchad battery (0%)

If you want to synchronize your todos, you'll needs something that syncs via
CalDAV. `vdirsyncer`_ is the recommended tool for this.

.. _vdirsyncer: https://vdirsyncer.readthedocs.org/en/stable/

Interactive shell
-----------------

If you install `click-repl <https://github.com/untitaker/click-repl>`_, todoman
gets a new command called ``repl``, which lauches an interactive shell with
tab-completion.
