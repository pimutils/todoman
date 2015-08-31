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
        open('requirements.txt').readlines()
    ],
    use_scm_version={'version_scheme': 'post-release'},
    setup_requires=['setuptools_scm'],
    # TODO: classifiers
)
