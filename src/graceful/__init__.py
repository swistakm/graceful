"""Minimalist framework for self-descriptive REST APIs build on top of falcon.

It is inspired by Django REST Framework package. Mostly by how object
serialization is done but more emphasis is put on API to be self-descriptive.
"""
VERSION = (0, 4, 1)  # PEP 386  # noqa
__version__ = ".".join([str(x) for x in VERSION])  # noqa
