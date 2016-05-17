# -*- coding: utf-8 -*-
VERSION = (0, 1, 2)  # PEP 386  # noqa
__version__ = ".".join([str(x) for x in VERSION])  # noqa

"""
Minimalist framework for self-descriptive RESTful APIs build on top of
falcon.

It is inspired by Django REST Framework package. Mostly by how object
serialization is done but more emphasis is put on API to being
self-descriptive.

"""
