#!/usr/bin/env python3

from setuptools import setup

setup(
    name='todoman',
    description='A simple CalDav-based todo manager.',
    author='Hugo Osvaldo Barrera',
    author_email='hugo@barrera.io',
    url='https://github.com/pimutils/todoman',
    license='ISC',
    packages=['todoman'],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'todo = todoman.cli:cli',
        ],
    },
    install_requires=[
        'atomicwrites',
        'click>=6.0',
        'click-log>=0.2.1',
        'configobj',
        'humanize',
        'icalendar>=4.0.3',
        'parsedatetime',
        'python-dateutil',
        'pyxdg',
        'tabulate',
        'urwid',
    ],
    long_description=open('README.rst').read(),
    use_scm_version={
        'version_scheme': 'post-release',
        'write_to': 'todoman/version.py',
    },
    setup_requires=['setuptools_scm'],
    tests_require=open('requirements-dev.txt').readlines(),
    extras_require={
        'docs': open('requirements-docs.txt').readlines(),
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Office/Business :: Scheduling',
        'Topic :: Utilities',
    ]
)
