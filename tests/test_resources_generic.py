# -*- coding: utf-8 -*-
import json

import pytest

from graceful.serializers import BaseSerializer
from graceful.fields import RawField
from graceful.resources.generic import (
    ListAPIResource,
    ObjectAPIResource,
    PaginatedListAPIResource)

# note: from now all definitions of resp and req must be annoteded with `noqa`
#       this is because py.test fixtures do not cooperate easily with flake8
from .test_fixtures import resp, req  # noqa


class ExampleSerializer(BaseSerializer):
    name = RawField('name', 'name of and entity')
    address = RawField('address', 'address of entity')


def test_list_resource_description(req, resp):  # noqa
    resource = ListAPIResource()

    description = resource.describe(req, resp)

    assert 'type' in description
    assert description['type'] == 'list'


def test_list_resource_implementation_hooks():
    resource = ListAPIResource()
    with pytest.raises(NotImplementedError):
        resource.get_list(None, None)


def test_list_resource_get(req, resp):  # noqa

    class InstanceListResource(ListAPIResource):
        serializer = ExampleSerializer()

        def get_list(self, params, meta, **kwargs):
            """
            Simulate that any object is retrieved
            """
            return [
                {
                    'name': "Johny",
                    'last_name': "Cage",
                    'address': "US",
                },
                {
                    'name': 'Monica',
                    'last_name': "Levinsky",
                    'address': "US",
                }
            ]

    resource = InstanceListResource()
    resource.on_get(req, resp)

    body = json.loads(resp.body)
    assert 'content' in body

    assert body['content'] == [
        {'name': "Johny", 'address': "US"},
        {'name': "Monica", 'address': "US"},
    ]

    assert 'meta' in body


def test_object_resource_description(req, resp):  # noqa
    resource = ObjectAPIResource()

    description = resource.describe(req, resp)

    assert 'type' in description
    assert description['type'] == 'object'


def test_object_resource_implementation_hooks():
    resource = ObjectAPIResource()
    with pytest.raises(NotImplementedError):
        resource.get_object(None, None)


def test_object_resource_get(req, resp):  # noqa

    class InstanceObjectResource(ObjectAPIResource):
        serializer = ExampleSerializer()

        def get_object(self, params, meta, **kwargs):
            """
            Simulate that any object is retrieved
            """
            return {
                'name': "Johny",
                'last_name': "Cage",
                'address': "US",
            }

    resource = InstanceObjectResource()
    resource.on_get(req, resp)

    body = json.loads(resp.body)
    assert 'content' in body
    assert body['content'] == {'name': "Johny", 'address': "US"}

    assert 'meta' in body


def test_paginated_list_resource(req, resp):  # noqa

    class PaginatedWithMore(PaginatedListAPIResource):
        serializer = ExampleSerializer()

        def get_list(self, params, meta, **kwargs):
            meta['has_more'] = True
            return [1, 0, 1]

    long_resource = PaginatedWithMore()
    long_resource.on_get(req, resp)
    body = json.loads(resp.body)

    assert len(body['content']) == 3
    # test since there is more then there should be also next in meta
    assert body['meta']['has_more']
    assert body['meta']['next']

    class PaginatedWithoutMore(PaginatedListAPIResource):
        serializer = ExampleSerializer()

        def get_list(self, params, meta, **kwargs):
            return [1, 0, 1]

    short_resource = PaginatedWithoutMore()
    short_resource.on_get(req, resp)
    body = json.loads(resp.body)

    assert len(body['content']) == 3
    # assert that if there is no 'has_more' specified then next
    # is automatically specified
    assert body['meta']['next']
