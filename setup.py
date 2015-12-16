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
            'todo = todoman.cli:cli',
        ]
    },
    install_requires=[
        open('requirements.txt').readlines()
    ],
    long_description=open('README.rst').read(),
    use_scm_version={
        'version_scheme': 'post-release',
        'write_to': 'todoman/version.py',
    },
    setup_requires=['setuptools_scm'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Topic :: Office/Business :: Scheduling',
        'Topic :: Utilities',
    ]
)
