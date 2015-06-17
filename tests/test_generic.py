# -*- coding: utf-8 -*-
from functools import wraps
import json
from unittest import TestCase

import pytest

from falcon.errors import HTTPNotFound
import falcon
from falcon.testing import TestBase

from graceful.serializers import BaseSerializer
from graceful.fields import RawField, IntField
from graceful.validators import min_validator
from graceful.resources.generic import (
    RetrieveAPI,
    RetrieveUpdateAPI,
    RetrieveUpdateDeleteAPI,
    ListAPI,
    ListCreateAPI,
    PaginatedListAPI,
    PaginatedListCreateAPI,
)


def index_error_as_404(fun):
    """
    Helper decorator that treats all IndexErrors as HTTP 404 Not Found

    :param fun: function/method to wrap
    :return:
    """
    @wraps(fun)
    def resource_handler(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except IndexError:
            raise HTTPNotFound

    return resource_handler


class TestSerializer(BaseSerializer):
    writable = RawField("testing writable field")
    readonly = RawField("testing readonly field", read_only=True)
    unsigned = IntField(
        "testing validated field",
        validators=[min_validator(0)]
    )


class StoredResource(object):
    def __init__(self, storage=None):
        self.storage = storage or []


class TestRetrieveAPI(RetrieveAPI, StoredResource):
    serializer = TestSerializer()

    @index_error_as_404
    def retrieve(self, params, meta, index, **kwargs):
        return self.storage[int(index)]


class TestRetrieveUpdateAPI(RetrieveUpdateAPI, StoredResource):
    serializer = TestSerializer()

    @index_error_as_404
    def retrieve(self, params, meta, index, **kwargs):
        return self.storage[int(index)]

    @index_error_as_404
    def update(self, params, meta, index, validated, **kwargs):
        self.storage[int(index)].update(validated)
        return validated


class TestRetrieveUpdateDeleteAPI(RetrieveUpdateDeleteAPI, StoredResource):
    serializer = TestSerializer()

    @index_error_as_404
    def retrieve(self, params, meta, index, **kwargs):
        return self.storage[int(index)]

    @index_error_as_404
    def update(self, params, meta, index, validated, **kwargs):
        self.storage[int(index)].update(validated)
        return validated

    @index_error_as_404
    def delete(self, params, meta, index, **kwargs):
        self.storage.pop(int(index))


class TestListAPI(ListAPI, StoredResource):
    serializer = TestSerializer()

    def list(self, params, meta, **kwargs):
        return self.storage


class TestListCreateAPI(ListCreateAPI, StoredResource):
    serializer = TestSerializer()

    def list(self, params, meta, **kwargs):
        return self.storage

    def create(self, params, meta, validated, **kwargs):
        self.storage.append(validated)
        return validated


class TestPaginatedListAPI(PaginatedListAPI, StoredResource):
    serializer = TestSerializer()

    def list(self, params, meta, **kwargs):
        start = params['page_size'] * (params['page'])
        end = params['page_size'] * (params['page'] + 1)
        return self.storage[start:end]


class TestPaginatedListCreateAPI(PaginatedListCreateAPI, StoredResource):
    serializer = TestSerializer()

    def list(self, params, meta, **kwargs):
        start = params['page_size'] * (params['page'])
        end = params['page_size'] * (params['page'] + 1)
        return self.storage[start:end]

    def create(self, params, meta, validated, **kwargs):
        self.storage.append(validated)
        return validated


class ImplementationHooksTests(TestCase):
    def test_update(self):
        with pytest.raises(NotImplementedError):
            RetrieveUpdateDeleteAPI().update(None, None)

    def test_retrieve(self):
        with pytest.raises(NotImplementedError):
            RetrieveUpdateDeleteAPI().retrieve(None, None)

    def test_delete(self):
        with pytest.raises(NotImplementedError):
            RetrieveUpdateDeleteAPI().delete(None, None)

    def test_list(self):
        with pytest.raises(NotImplementedError):
            PaginatedListCreateAPI().list(None, None)

    def test_create(self):
        with pytest.raises(NotImplementedError):
            PaginatedListCreateAPI().create(None, None)


class GenericsTestBase(TestBase):
    def setUp(self):
        super(GenericsTestBase, self).setUp()

        self.storage = [{"writeble": "foo", "readonly": "bar"}]

    def _assert_consistent_form(self, result):
        body = json.loads(result)

        assert self.srmock.headers_dict['Content-Type'] == 'application/json'
        assert body
        assert 'meta' in body
        assert 'content' in body


class RetrieveTestsMixin(object):
    """
    Contains all test that should be performed on Resource that supports
    retrieve
    """
    def test_retrieve(self):
        result = self.simulate_request('/items/0', decode='utf-8')
        self._assert_consistent_form(result)

        assert self.srmock.status == falcon.HTTP_OK

    def test_retrieve_not_found(self):
        # note: only one item in storage so this will return 404
        self.simulate_request('/items/1', decode='utf-8')
        assert self.srmock.status == falcon.HTTP_NOT_FOUND


class UpdateTestsMixin(object):
    """
    Contains all test that should be performed on Resource that supports
    update
    """
    def do_update(self, index_, representation):
        return self.simulate_request(
            '/items/{}'.format(index_),
            decode='utf-8',
            method='PUT',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(representation),
        )

    def test_update(self):
        result = self.do_update(0, {'writable': 'changed', 'unsigned': 12})
        self._assert_consistent_form(result)
        assert self.srmock.status == falcon.HTTP_ACCEPTED

        body = json.loads(result)
        assert body['content']['writable'] == 'changed'

    def test_update_not_found(self):
        self.do_update(1, {'writable': 'changed', 'unsigned': 12})
        assert self.srmock.status == falcon.HTTP_NOT_FOUND

    def test_update_readonly_field_error(self):
        self.do_update(
            0, {'writable': 'changed', 'unsigned': 12, 'readonly': 'changed'}
        )
        assert self.srmock.status == falcon.HTTP_BAD_REQUEST

    def test_update_missing_field_error(self):
        self.do_update(0, {'writable': 'changed'})
        assert self.srmock.status == falcon.HTTP_BAD_REQUEST

    def test_update_parse_error(self):
        # note: 'unsigned' that can't be parsed
        self.do_update(0, {'writable': 'changed', 'unsigned': 'foo'})
        assert self.srmock.status == falcon.HTTP_BAD_REQUEST

    def test_update_validation_error(self):
        # note: 'unsigned' that is < 0
        self.do_update(0, {'writable': 'changed', 'unsigned': -12})
        assert self.srmock.status == falcon.HTTP_BAD_REQUEST

    def test_update_unsuported_media_type(self):
        self.simulate_request(
            '/items/0',
            decode='utf-8',
            method='PUT',
            headers={'Content-Type': 'unsupported'},
            body="foo bar",
        )
        assert self.srmock.status == falcon.HTTP_UNSUPPORTED_MEDIA_TYPE


class DeleteTestsMixin(object):
    """
    Contains all test that should be performed on resource that supports
    delete
    """
    def do_delete(self, index_):
        return self.simulate_request(
            '/items/{}'.format(index_),
            decode='utf-8',
            method='DELETE',
        )

    def test_delete(self):
        response = self.do_delete(0)
        self._assert_consistent_form(response)
        assert self.storage == []

    def test_delete_not_found(self):
        self.do_delete(1)
        assert self.srmock.status == falcon.HTTP_NOT_FOUND


class ListTestsMixin(object):
    """
    Contains all tests that should be performed on resource that supports list
    """
    def test_list(self):
        result = self.simulate_request('/items/', decode='utf-8')
        self._assert_consistent_form(result)

        assert self.srmock.status == falcon.HTTP_OK


class PaginationTestsMixin(object):
    def test_list_pagination(self):
        for _ in range(100):
            self.storage.append({"writeble": "foo", "readonly": "bar"})

        result = self.simulate_request('/items/', decode='utf-8')
        body = json.loads(result)

        assert 'next' in body['meta']
        assert 'prev' in body['meta']
        assert len(body['content']) == body['meta']['page_size']

        # now try to access page without results
        result = self.simulate_request(
            '/items/', decode='utf-8', query_string="page=1000"
        )
        body = json.loads(result)
        assert len(body['content']) == 0


class CreateTestsMixin():
    """
    Contains all tests that should be performed on resource that suports create
    """
    def do_create(self, representation):
        return self.simulate_request(
            '/items/',
            decode='utf-8',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(representation),
        )

    def test_create(self):
        result = self.do_create(
            {'writable': 'changed', 'unsigned': 12}
        )
        self._assert_consistent_form(result)

        assert self.srmock.status == falcon.HTTP_CREATED

    def test_create_readonly_field_error(self):
        self.do_create(
            {'writable': 'changed', 'unsigned': 12, 'readonly': 'changed'}
        )
        assert self.srmock.status == falcon.HTTP_BAD_REQUEST

    def test_create_missing_field_error(self):
        self.do_create({'writable': 'changed'})
        assert self.srmock.status == falcon.HTTP_BAD_REQUEST

    def test_create_parse_error(self):
        # note: 'unsigned' that can't be parsed
        self.do_create({'writable': 'changed', 'unsigned': 'foo'})
        assert self.srmock.status == falcon.HTTP_BAD_REQUEST

    def test_create_validation_error(self):
        # note: 'unsigned' that is < 0
        self.do_create({'writable': 'changed', 'unsigned': -12})
        assert self.srmock.status == falcon.HTTP_BAD_REQUEST

    def test_create_unsuported_media_type(self):
        self.simulate_request(
            '/items/',
            decode='utf-8',
            method='POST',
            headers={'Content-Type': 'unsupported'},
            body="foo bar",
        )
        assert self.srmock.status == falcon.HTTP_UNSUPPORTED_MEDIA_TYPE


# actual test cases classes here

class RetrieveTestCase(
    RetrieveTestsMixin,
    GenericsTestBase,
):
    def setUp(self):
        super(RetrieveTestCase, self).setUp()
        self.api.add_route(
            '/items/{index}',
            TestRetrieveAPI(self.storage)
        )


class RetrieveUpdateTestCase(
    RetrieveTestsMixin,
    UpdateTestsMixin,
    GenericsTestBase,
):
    def setUp(self):
        super(RetrieveUpdateTestCase, self).setUp()
        self.api.add_route(
            '/items/{index}',
            TestRetrieveUpdateAPI(self.storage)
        )


class RetrieveUpdateDeleteTestCase(
    RetrieveTestsMixin,
    UpdateTestsMixin,
    DeleteTestsMixin,
    GenericsTestBase,
):
    def setUp(self):
        super(RetrieveUpdateDeleteTestCase, self).setUp()
        self.api.add_route(
            '/items/{index}',
            TestRetrieveUpdateDeleteAPI(self.storage)
        )


class ListTestCase(
    ListTestsMixin,
    GenericsTestBase,
):
    def setUp(self):
        super(ListTestCase, self).setUp()
        self.api.add_route(
            '/items/',
            TestListAPI(self.storage)
        )


class ListCreateTestCase(
    ListTestsMixin,
    CreateTestsMixin,
    GenericsTestBase,
):
    def setUp(self):
        super(ListCreateTestCase, self).setUp()
        self.api.add_route(
            '/items/',
            TestListCreateAPI(self.storage)
        )


class PaginatedListTestCase(
    ListTestsMixin,
    PaginationTestsMixin,
    GenericsTestBase,
):
    def setUp(self):
        super(PaginatedListTestCase, self).setUp()
        self.api.add_route(
            '/items/',
            TestPaginatedListAPI(self.storage)
        )


class PaginatedListCreateTestCase(
    ListTestsMixin,
    CreateTestsMixin,
    PaginationTestsMixin,
    GenericsTestBase,
):
    def setUp(self):
        super(PaginatedListCreateTestCase, self).setUp()
        self.api.add_route(
            '/items/',
            TestPaginatedListCreateAPI(self.storage)
        )
