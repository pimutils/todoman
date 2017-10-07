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

We strictly follow the `Style Guide for Python Code`_, which I strongly
recommend you read, though you may simply run ``flake8`` to verify that your
code is compliant.

Commits should follow `Git Commit Guidelines`_ whenever possible, including
rewriting branch histories to remove any noise, and using a 50-message
imperative present tense for commit summary messages.

All commits should pass all tests to facilitate bisecting in future.

.. _Style Guide for Python Code: http://python.org/dev/peps/pep-0008/
.. _Git Commit Guidelines: https://www.git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project#_commit_guidelines

An overview of the Todo lifecycle
---------------------------------

This is a brief overview of the life cycles of todos (from the apps point of
view) as they are read from disk, displayed, and or saved again.

When the app starts, it will read all todos from disk, and initialize from the
cache any further display (either ``list``, ``show``, ``edit``, etc) is then
done reading from the cache, which only contains the fields we operate with.

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

Patch review checklist
~~~~~~~~~~~~~~~~~~~~~~

Please follow this checklist when submitting new PRs (or reviewing PRs by
others):

#. Do all tests pass?
#. Does the documentation build?
#. Does the coding style conform to our guidelines? Are there any flake8 errors?
#. Are user-facing changes documented?
#. Is there an entry for new features or dependencies in ``CHANGELOG.rst``?
#. Are you the patch author? Are you listed in ``AUTHORS.rst``?

*Hint: To quickly verify the first three items run* ``tox``.

Authorship
----------

While authors must add themselves to ``AUTHORS.rst``, all copyright is retained
by them. Contributions are accepted under the :doc:`ISC licence <licence>`.
