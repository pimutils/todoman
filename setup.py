#!/usr/bin/env python3

from setuptools import setup

setup(
    name='todoman',
    description='A simple CalDav-based todo manager.',
    author='Hugo Osvaldo Barrera',
    author_email='hugo@barrera.io',
    url='https://gitlab.com/hobarrera/todoman',
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
        'setuptools_scm',
    ],
    use_scm_version={'version_scheme': 'post-release'},
    setup_requires=['setuptools_scm'],
    # TODO: classifiers
)
