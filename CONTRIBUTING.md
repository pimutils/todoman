Contributing
============

Bug reports and code and documentation patches are greatly appreciated. You can
also help by using the development version of todoman and reporting any bugs
you might encounter [here](https://github.com/pimutils/todoman/issues).

Note that all participants must follow the [pimutils Code of
Conduct](http://pimutils.org/coc).


Code and Documentation
----------------------

Before working on a new feature or a bug, please browse existing issues
to see whether it has been previously discussed. If the change in question
is a bigger one, it's always good to open a new issue to discuss it before your
starting working on it.


Development
-----------

Runtime dependencies are listed in [requirements.txt][requirements]. I
recommend that you use virtualenv to make sure that no additional dependencies
are required without them being properly documented.

Code contributions should also pass flake8 (pep8 and pyflakes). If you're
unfamiliar with these, the [Style Guide for Python Code][pep8] is a highly
recommended read.

Commits should follow git's [guidelines][git-guidelines] whenever possible,
including rewriting branch histories to remove any noise, and using a
50-message imperative present tense for commit summary messages.

Tests
-----

There is very little unit test coverage for now, and they can be run via
[tox][tox]. Any bugfixes should include a test which would fail without the fix
applied.

[requirements]: requirements.txt
[pep8]: http://python.org/dev/peps/pep-0008/
[tox]: http://tox.testrun.org
[git-guidelines]: https://www.git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project#Commit-Guidelines
