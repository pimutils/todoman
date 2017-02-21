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

Runtime dependencies are listed in ``requirements.txt``. I recommend that you
use virtualenv to make sure that no additional dependencies are required
without them being properly documented.

We strictly follow the `Style Guide for Python Code`_, which I strongly
recommend you read, though you may simply run ``flake8`` to verify that your
code is compliant.

Commits should follow `Git Commit Guidelines`_ whenever possible, including
rewriting branch histories to remove any noise, and using a 50-message
imperative present tense for commit summary messages.

All commits should pass all tests to facilitate bisecting in future.

.. _Style Guide for Python Code: http://python.org/dev/peps/pep-0008/
.. _Git Commit Guidelines: https://www.git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project#_commit_guidelines

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
