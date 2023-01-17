#!/usr/bin/env python3
from setuptools import setup

with open("README.rst") as r:
    long_description = r.read()
with open("requirements-dev.txt") as r:
    tests_require = r.readlines()
with open("requirements-docs.txt") as r:
    docs = r.readlines()

setup(
    name="todoman",
    description="A simple icalendar-based todo manager.",
    author="Hugo Osvaldo Barrera",
    author_email="hugo@barrera.io",
    url="https://github.com/pimutils/todoman",
    license="ISC",
    packages=["todoman"],
    include_package_data=True,
    entry_points={"console_scripts": ["todo = todoman.cli:cli"]},
    install_requires=[
        "atomicwrites",
        "click>=7.1,<9.0",
        "click-log>=0.2.1",
        "humanize",
        "icalendar>=4.0.3",
        "parsedatetime",
        "python-dateutil",
        "pyxdg",
        "urwid",
    ],
    long_description=long_description,
    setup_requires=["setuptools_scm"],
    tests_require=tests_require,
    extras_require={
        "docs": docs,
        "repl": ["click-repl>=0.1.6"],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Console :: Curses",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Office/Business :: Scheduling",
        "Topic :: Utilities",
    ],
)
