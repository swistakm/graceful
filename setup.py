# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import os


def get_version(version_tuple):
    if not isinstance(version_tuple[-1], int):
        return '.'.join(map(str, version_tuple[:-1])) + version_tuple[-1]
    return '.'.join(map(str, version_tuple))


init = os.path.join(
    os.path.dirname(__file__),
    'src', 'graceful', '__init__.py'
)
version_line = list(filter(lambda l: l.startswith('VERSION'), open(init)))[0]
VERSION = get_version(eval(version_line.split('=')[-1]))

INSTALL_REQUIRES = [
    'falcon'
]

try:
    from pypandoc import convert

    def read_md(f):
        return convert(f, 'rst')

except ImportError:
    convert = None
    print(
        "warning: pypandoc module not found, could not convert Markdown to RST"
    )

    def read_md(f):
        return open(f, 'r').read()  # noqa

README = os.path.join(os.path.dirname(__file__), 'README.md')
PACKAGES = find_packages('src')
PACKAGE_DIR = {'': 'src'}

setup(
    name='graceful',
    version=VERSION,
    author='Michał Jaworski',
    author_email='swistakm@gmail.com',
    description='falcon REST done with grace',
    long_description=read_md(README),
    packages=PACKAGES,
    package_dir=PACKAGE_DIR,

    url='https://github.com/swistakm/graceful',
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    zip_safe=True,

    license="BSD",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Application Frameworks',

        'Programming Language :: Python',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
    ],
)
