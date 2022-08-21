Contributing
============

Bug reports and code and documentation patches are greatly appreciated. You can
also help by using the development version of todoman and reporting any bugs
you might encounter `here <https://github.com/pimutils/todoman/issues>`_.

All participants must follow the pimutils `Code of Conduct
<http://pimutils.org/coc>`_.

Before working on a new feature or a bug, please browse existing issues to see
whether it has been previously discussed. If the change in question is a bigger
one, it's always good to open a new issue to discuss it before your starting
working on it.

Hacking
~~~~~~~

Runtime dependencies are listed in ``setup.py``. We recommend that you use
virtualenv to make sure that no additional dependencies are required without
them being properly documented.
Run ``pip install -e .`` to install todoman and its dependencies into a
virtualenv.

We use ``pre-commit`` to run style and convention checks. Run ``pre-commit
install``` to install our git-hooks. These will check code style and inform you
of any issues when attempting to commit. This will also run ``black`` to
reformat code that may have any inconsistencies.

Commits should follow `Git Commit Guidelines`_ whenever possible, including
rewriting branch histories to remove any noise, and using a imperative present
tense for commit summary messages (50 characters maximum).

All commits should pass all tests to facilitate bisecting in future.

.. _Git Commit Guidelines: https://www.git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project#_commit_guidelines

An overview of the Todo lifecycle
---------------------------------

This is a brief overview of the life cycles of todos (from the apps point of
view) as they are read from disk, displayed, and or saved again.

When the app starts, it will read all todos from disk, and initialize from the
cache any further display (either ``list``, ``show``, ``edit``, etc) is then
done reading from the cache, which only contains the fields with which we
operate. This stage also assigns the id numbers to each todo.

When a Todo is edited, the entire cycle is:

* File is read from disk and cached (if not already cached).
* A Todo object is created by reading the cache.
* If edition is interactive, show the UI now.
* No matter how the edition occurs, apply changes to the Todo object.
* Start saving process:
   * Read file from disk (as a VTodo object).
   * Apply changes from fields to the VTodo object.
   * Write to disk.

The main goal of this is to simplify how many conversions we have. If we read
from disk to the editor, we'd need an extra VTodo->Todo conversion code that
skips the cache.

Running and testing locally
---------------------------

The easiest way to run tests, it to install ``tox``, and then simply run
``tox``. By default, several python versions and environments are tested. If
you want to run a specific one use ``tox -e ENV``, where ``ENV`` should be one
of the environments listed by ``tox -l``.

See the `tox`_ documentation for further details.

To run your modified copy of ``todoman`` without installing it, it's
recommended you set up a virtualenv, and run ``pip install -e .`` to install
your checked-out copy into it (this'll make ``todo`` run your local copy while
the virtualenv is active).

.. _tox: http://tox.readthedocs.io/en/latest/

Authorship
----------

Authors may add themselves to ``AUTHORS.rst``, and all copyright is retained by
them. Contributions are accepted under the :doc:`ISC licence <licence>`.

Patch review checklist
~~~~~~~~~~~~~~~~~~~~~~

Please follow this checklist when submitting new PRs (or reviewing PRs by
others):

CI will automatically check these for us:

#. Do all tests pass?
#. Does the documentation build?
#. Do all linting and style checks pass?

Please keep an eye open for these other items:

#. If any features have changed, make sure the docs reflect this.
#. If there are any user-facing changes, make sure the :doc:`changelog` reflects this.
#. If there are any dependency changes, make sure the :doc:`changelog` reflects this.
#. If not already present, please add yourself to ``AUTHORS.rst``.

Packaging
~~~~~~~~~

We appreciate distributions packaging todoman. Packaging should be relatively
straightforward following usual Python package guidelines. We recommend that
you git-clone tags, and build from source, since these tags are GPG signed.

Dependencies are listed in ``setup.py``. Please also try to include the
extras dependencies as optional dependencies (or what maps best for your
distribution).

You'll need to run ``python setup.py build`` to generate the
``todoman/version.py`` file which is necessary at runtime.

We recommend that you include the :doc:`man` in distribution packages. You can
build this by running::

    sphinx-build -b man docs/source docs/build/man

The man page will be saved as `docs/build/man/todo.1`.

Generating the man pages requires that todoman and its doc dependencies (see
``requirements-docs.txt``) are either installed, or in the current
``PYTHONPATH``.
