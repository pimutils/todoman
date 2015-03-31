#!/usr/bin/env python

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
            'todo = todoman.main:main',
        ]
    },
    install_requires=[
        'docopt',
        'icalendar',
        'urwid',
        'pyxdg',
        'atomicwrites'
    ],
    # TODO: classifiers
)
