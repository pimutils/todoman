#!/usr/bin/env python3

import todoman
from todoman.configuration import CONFIG_SPEC
from todoman.configuration import NO_DEFAULT

# -- Generate confspec.rst ----------------------------------------------


def confspec_rst():
    """Generator that returns lines for the confspec doc page."""

    for name, type_, default, description, _validation in sorted(CONFIG_SPEC):
        if default == NO_DEFAULT:
            formatted_default = "None, this field is mandatory."
        elif isinstance(default, str):
            formatted_default = f'``"{default}"``'
        else:
            formatted_default = f"``{default}``"

        yield f"\n.. _main-{name}:"
        yield f"\n\n.. object:: {name}\n"
        yield "    " + "\n    ".join(line for line in description.splitlines())
        yield "\n\n"

        if isinstance(type_, tuple):
            yield f"      :type: {type_[0].__name__}"
        else:
            yield f"      :type: {type_.__name__}"

        yield f"\n      :default: {formatted_default}\n"


with open("confspec.tmp", "w") as file_:
    file_.writelines(confspec_rst())

# -- General configuration ------------------------------------------------

extensions = [
    "sphinx_click.ext",
    "sphinx.ext.autodoc",
    "sphinx_autorun",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_rtd_theme",
]

source_suffix = ".rst"

master_doc = "index"

project = "Todoman"
copyright = "2015-2020, Hugo Osvaldo Barrera"
author = "Hugo Osvaldo Barrera <hugo@barrera.io>, et al"

# The short X.Y version.
version = todoman.__version__
# The full version, including alpha/beta/rc tags.
release = todoman.__version__

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# -- Options for HTML output ----------------------------------------------

html_theme = "sphinx_rtd_theme"

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (
        "man",
        "todo",
        "a simple, standards-based, cli todo manager",
        [author],
        1,
    )
]
