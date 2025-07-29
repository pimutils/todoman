Installing
==========

Distribution packages
---------------------

If todoman is packaged for your OS/distribution, using your system's
standard package manager is probably the easiest way to install todoman.

ArchLinux
~~~~~~~~~

todoman is packaged in the community_ repository, and can be installed using::

    pacman -S todoman

.. _community: https://www.archlinux.org/packages/community/any/todoman/

homebrew (macOS)
~~~~~~~~~~~~~~~~

todoman is packaged in homebrew_, and can be installed using::

    brew install todoman

.. _homebrew: https://formulae.brew.sh/formula/todoman

PyPI (installatoin via pip)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since *todoman* is written in python, you can use python's package managers,
*pip* by executing::

    pip install todoman

or the latest development version by executing::

     pip install git+git://github.com/pimutils/todoman.git

This should also take care of installing all required dependencies.

Manual installation
-------------------

If pip is not available either (this is most unlikely), you'll need to download
the source tarball and install via pip, though this is not a recommended
installation method::

    pip install -e .

bash autocompletion (optional)
------------------------------

There is an autocompletion function for bash provided in the ``contrib``
directory. If you want to enable autocompletion for todoman in bash, copy the
file ``contrib/autocompletion/bash/_todo`` to any directory you want. Typically
``/etc/bash_completion.d`` is used for system-wide installations or
``~/.bash_completion.d`` for local installations. In the former case, the file
is automatically sourced in most distributions, in the latter case, you will
most likely need to add::

    source ~/.bash_completion.d/_todo

to your ``~/.bashrc``.


zsh autocompletion (optional)
-----------------------------

There is an autocompletion function for zsh provided in the ``contrib``
directory. If you want to enable autocompletion for todoman in zsh, copy the
file ``contrib/autocompletion/zsh/_todo`` to any directory in your ``$fpath``.
Typically ``/usr/local/share/zsh/site-functions/`` is used for system-wide
installations.

Requirements
------------

Todoman requires python 3.9 or later. Installation of required libraries can be
done via pip, or your OS's package manager.

Recent versions also have experimental support for pypy3.

.. _notes-for-packagers:

Notes for Packagers
-------------------

All of todoman's dependencies are listed in the ``dependencies`` section of
the pyproject.toml_ file. New dependencies will be clearly announced in the
``CHANGELOG.rst`` file for each release. Patch releases (eg: those where only
the third digit of the version is incremented) **will not** introduce new
dependencies.

.. _pyproject.toml: https://github.com/pimutils/todoman/blob/main/pyproject.toml

Additionally, `jq` is dependency for zsh's autocompletion. For platforms where
`zsh` is the default shell, it is recommended to list `jq` as a dependency, for
others adding it as an optional dependency should suffice.

A wheel can be build with::

   python -m build

It can then be installed with::

   python3 -m installer .dist/*.whl

When packaging, you usually want to install to a custom directory, rather than
the root filesystem. For this, use ``-d``::

   python3 -m installer -d "$pkgdir" .dist/*.whl
