Usage
=====

Todoman usage is `CLI`_ based (thought there are some TUI bits, and the
intentions is to also provide a fully `TUI`_-based interface).

The default action is ``list``, which outputs all tasks for all calendars, each
with a semi-permanent unique id::

    1 [ ] !!! 2015-04-30 Close bank account @work (0%)
    2 [ ] !              Send minipimer back for warranty replacement @home (0%)
    3 [X]     2015-03-29 Buy soy milk @home (100%)
    4 [ ] !!             Fix the iPad's screen @home (0%)
    5 [ ] !!             Fix the Touchpad battery @work (0%)

The columns, in order, are:

 * An id.
 * Whether the task has been completed or not.
 * An ``!!!`` indicating high priority, ``!!`` indicating medium priority,
   ``!`` indicating low priority tasks.
 * The due date.
 * The task summary.
 * The list the todo is from; it will be hidden when filtering by one list, or
   if the database only contains a single list.
 * The completed percentage.

The id is retained by ``todoman`` until the next time you run the ``flush``
command.

To operate on a todo, the id is what's used to reference it. For example, to
edit the `Buy soy milk` task from the example above, the proper command is
``todo edit 3``, or ``todo undo 3`` to un-mark the task as done.

Editing tasks can only be done via the TUI interface for now, and cannot be
done via the command line yet.

.. _cli: https://en.wikipedia.org/wiki/Command-line_interface
.. _tui: https://en.wikipedia.org/wiki/Text-based_user_interface


Synchronization
---------------

If you want to synchronize your tasks, you'll need something that syncs via
CalDAV. `vdirsyncer`_ is the recommended tool for this.

.. _vdirsyncer: https://vdirsyncer.readthedocs.org/en/stable/

Interactive shell
-----------------

If you install `click-repl <https://github.com/untitaker/click-repl>`_, todoman
gets a new command called ``repl``, which launches an interactive shell with
tab-completion.

Integrations
------------

When attempting to integrate ``todoman`` into other systems or parse its
output, you're advised to use the ``--porcelain`` flag, which will print all
output in a pre-defined format that will remain stable regardless of user
configuration or version.

The format is JSON, with a single array containing each todo as a single entry
(object). Fields will always be present; if a todo does not have a value for a
given field, it will be printed as ``null``.

Fields MAY be added in future, but will never be removed.

Conky
`````

Todoman can be used with `Conky`_  by using one of the shell execution
`variables`_.
Given the nature of pimutils utilities, there is no need to query new information
every time conky updates so ``execi`` will be the best option most of the time.

Adding ``${execi 30 todo}`` inside the text section will display the output of the
command and update it every 30 seconds.

A working configuration can be found `here`_.

.. _conky: https://conky.cc
.. _variables: https://conky.sourceforge.net/variables.html
.. _here: https://github.com/r4ulill0/todoman/blob/main/docs/examples/conky.conf

Sorting
-------

The tasks can be sorted with the ``--sort`` argument. Sorting may be done according to the following fields:

    - ``description``
    - ``location``
    - ``status``
    - ``summary``
    - ``uid``
    - ``rrule``
    - ``percent_complete``
    - ``priority``
    - ``sequence``
    - ``categories``
    - ``completed_at``
    - ``created_at``
    - ``dtstamp``
    - ``start``
    - ``due``
    - ``last_modified``
