#!/usr/bin/env python

from setuptools import setup

setup(
    name='todoman',
    # TODO: Move this to VERSION:
    version='1.0.0',
    description='A simple CalDav-based todo manager.',
    author='Hugo Osvaldo Barrera',
    author_email='hugo@barrera.io',
    url='https://git.barrera.io/hobarrera/todoman',
    license='MIT',
    packages=['todoman'],
    entry_points={
        'console_scripts': [
            'todo = todoman:main',
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
