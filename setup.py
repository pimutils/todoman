#!/usr/bin/env python3

from setuptools import setup

setup(
    name='todoman',
    description='A simple CalDav-based todo manager.',
    author='Hugo Osvaldo Barrera',
    author_email='hugo@barrera.io',
    url='https://github.com/pimutils/todoman',
    license='MIT',
    packages=['todoman'],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'todo = todoman.cli:cli',
        ]
    },
    install_requires=open('requirements.txt').readlines(),
    long_description=open('README.rst').read(),
    use_scm_version={
        'version_scheme': 'post-release',
        'write_to': 'todoman/version.py',
    },
    setup_requires=['setuptools_scm != 1.12.0', 'pytest-runner'],
    tests_require=open('requirements-dev.txt').readlines(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Office/Business :: Scheduling',
        'Topic :: Utilities',
    ]
)
