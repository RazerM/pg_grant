import re

from setuptools import setup, find_packages


INIT_FILE = 'pg_grant/__init__.py'
init_data = open(INIT_FILE).read()

metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", init_data))

VERSION = metadata['version']
LICENSE = metadata['license']
DESCRIPTION = metadata['description']
AUTHOR = metadata['author']
EMAIL = metadata['email']

requires = [
    'attrs',
]

extras_require = {
    ':python_version<"3.5"': [
        'typing',
    ],
    'sqlalchemy': [
        'sqlalchemy[postgresql]',
    ],
    'test': [
        'plumbum',
        'pytest>=3.0',
        'testcontainers[postgresql,selenium]',
        'testing.postgresql',
    ],
    'docstest': [
        'doc8',
        'sphinx',
        'sphinx_rtd_theme',
    ],
    'pep8test': [
        'flake8',
        'pep8-naming',
    ],
}

setup(
    name='pg_grant',
    version=VERSION,
    description=DESCRIPTION,
    long_description=open('README.rst').read(),
    author=AUTHOR,
    author_email=EMAIL,
    url='https://github.com/RazerM/pg_grant',
    packages=find_packages(exclude=['tests']),
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    license=LICENSE,
    install_requires=requires,
    extras_require=extras_require,
    tests_require=extras_require['test'])
