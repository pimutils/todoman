Installing
==========

If todoman is packaged for your OS/distribution, using your system's
standard package manager is probably the easiest way to install khal:

- ArchLinux (AUR_)

.. _AUR: https://aur.archlinux.org/packages/todoman/

Install via PIP
---------------

Since *todoman* is written in python, you can use python's package managers,
*pip* by executing::

    pip install todoman

or the latest development version by executing::

     pip install git+git://github.com/pimutils/todoman.git

This should also take care of installing all required dependencies.

Manual installation
-------------------

If pip is not available either (this is most unlikely), you'll need to download
the source tarball and install via setup.py, though this is not a recomended
installation method::

    python3 setup.py install

Requirements
------------

Todoman requires python 3.3 or later. Installation of required libraries can be
done via pip, or your OS's package manager. If you're interested in packaging
todoman, all depenencies are listed in requirements.txt_.

Todoman will not work with python 2. However, keep in mind that python 2 and
python 3 can coexist (and most distributions actually ship both).


.. _requirements.txt: https://github.com/pimutils/todoman/blob/master/requirements.txt
