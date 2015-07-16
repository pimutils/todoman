#!/usr/bin/env python3

from setuptools import setup

import todoman

setup(
    name='todoman',
    version=todoman.__version__,
    description='A simple CalDav-based todo manager.',
    author='Hugo Osvaldo Barrera',
    author_email='hugo@barrera.io',
    url='https://git.barrera.io/hobarrera/todoman',
    license='MIT',
    packages=['todoman'],
    entry_points={
        'console_scripts': [
            'todo = todoman.cli:run',
        ]
    },
    install_requires=[
        'click',
        'icalendar',
        'urwid',
        'pyxdg',
        'atomicwrites',
        # https://github.com/tehmaze/ansi/pull/7
        'ansi>=0.1.3',
        'parsedatetime',
    ],
    # TODO: classifiers
)
