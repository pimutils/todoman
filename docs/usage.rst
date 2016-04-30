Usage
=====

Todoman usage is `CLI`_ based (thought there are some TUI bits, and the
intentions is to also provide a fully `TUI`_-based interface).

First of all, the classic usage output::

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
      shell  Start an interactive shell.
      show   Show details about a task.

The default action is ``list``, which outputs all tasks for all calendars, each
with a non-permanent unique id::

    1 [ ] ! 2015-04-30 Close bank account (0%)
    2 [ ] !            Send minipimer back for warranty replacement (0%)
    3 [X]   2015-03-29 Buy soy milk (100%)
    4 [ ]              Fix the iPad's screen (0%)
    5 [ ]              Fix the Touchad battery (0%)

The columns, in order, are:

 * A temporary id.
 * Whether the task has been completed or not.
 * An ``!`` indicating it's an urgent task.
 * The due date
 * The task summary
 * The completed percentage

The temporary id is retained by ``todoman`` until the next time you run the
``list`` command (remember: it's the default command is no other is specified).

To operate on a todo, the id is what's used to reference it. For example, to
edit the `Buy soy milk` task from the example above, the proper command is
``todo edit 3``, or ``todo undo 3`` to un-mark the task as done.

Editing tasks can only be done via the TUI interface for now, and cannot be
done via the command line yet.

.. _cli: https://en.wikipedia.org/wiki/Command-line_interface
.. _tui: https://en.wikipedia.org/wiki/Text-based_user_interface


Synchronization
---------------

If you want to synchronize your tasks, you'll needs something that syncs via
CalDAV. `vdirsyncer`_ is the recommended tool for this.

.. _vdirsyncer: https://vdirsyncer.readthedocs.org/en/stable/

Interactive shell
-----------------

If you install `click-repl <https://github.com/untitaker/click-repl>`_, todoman
gets a new command called ``repl``, which lauches an interactive shell with
tab-completion.
