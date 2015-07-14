# -*- coding: utf-8 -*-
import copy
import json
from collections.abc import Iterable

from falcon.testing import create_environ
from falcon import Request
from falcon import errors
import falcon
import pytest

from graceful.errors import ValidationError
from graceful.resources.generic import Resource
from graceful.parameters import StringParam, BaseParam
from graceful.serializers import BaseSerializer
from graceful.fields import StringField


class TestResource(Resource):
    def retrieve(self, params, meta, **kwargs):
        return None


def test_base_resource_get(req, resp):
    """
    Test that simple resource GET will return 200 OK response with JSON encoded
    body.

    :param req: falcon.Request object provided by `req` pytest fixture
    :param resp: falcon.Response object provided by`resp` pytest fixture
    """
    resource = TestResource()

    resource.on_get(req, resp)

    assert resp.content_type == "application/json"
    assert resp.body
    assert resp.status == falcon.HTTP_200


def test_resource_indent(req, resp):
    resource = TestResource()

    # default: without indent
    resource.on_get(req, resp)
    assert "    " not in resp.body
    assert "\n" not in resp.body

    # with explicit indent
    req.params['indent'] = '4'
    resource.on_get(req, resp)
    assert "    " in resp.body


def test_resource_meta(req, resp):
    """
    Test if meta output part on resource GET has a desired structure

    :param req: falcon.Request object provided by `req` pytest fixture
    :param resp: falcon.Response object provided by`resp` pytest fixture
    """
    resource = TestResource()
    resource.on_get(req, resp)

    body = json.loads(resp.body)

    assert 'meta' in body
    assert 'params' in body['meta']


def test_required_params(req, resp):
    """
    Test that when params are missing then specific falcon exception is raised
    and thus proper status code will be returned.

    :param req: falcon.Request object provided by `req` pytest fixture
    :param resp: falcon.Response object provided by`resp` pytest fixture
    """
    class ParametrizedResource(TestResource):
        foo = StringParam(details="required foo!", required=True)

    resource = ParametrizedResource()

    with pytest.raises(errors.HTTPMissingParam):
        resource.on_get(req, resp)

    param_req = copy.copy(req)
    param_req.params['foo'] = 'bar'
    resource.on_get(req, resp)
    assert resp.status == falcon.HTTP_OK


def test_resource_accepts_kwargs(req, resp):
    """
    Test that on_get method accepts additional keyword arguments.
    This is important because allows passing of arguments from url template.

    :param req: falcon.Request object provided by `req` pytest fixture
    :param resp: falcon.Response object provided by`resp` pytest fixture
    """
    resource = TestResource()
    resource.on_get(req, resp, foo='bar')


def test_describe(req, resp):
    """
    Test if output of resource.description() has desired form.

    :param req: falcon.Request object provided by `req` pytest fixture
    :param resp: falcon.Response object provided by`resp` pytest fixture
    """
    # default description keys
    resource = Resource()
    description = resource.describe(req, resp)
    assert 'path' in description
    assert 'name' in description
    assert 'details' in description
    assert 'params' in description
    assert 'methods' in description

    # test extending of description through kwargs
    assert 'foo' not in description
    description = resource.describe(req, resp, foo='bar')
    assert 'foo' in description
    assert description['foo'] == 'bar'


def test_options(resp):
    """
    Test that options is a json serialized output of resource.describe()

    :param req: falcon.Request object provided by `req` pytest fixture
    :param resp: falcon.Response object provided by`resp` pytest fixture
    """
    # note: creating request is optional here since we bypass whole falcon
    #       routing and dispatching procedure
    env = create_environ(method="OPTIONS")
    req = Request(env)   # noqa
    resource = Resource()

    resource.on_options(req, resp)

    assert resp.status == falcon.HTTP_200
    assert json.loads(resp.body)
    # assert this is obviously the same
    assert resource.describe(req, resp) == json.loads(resp.body)


def test_options_with_additional_args(req, resp):
    """
    Test that requesting OPTIONS will succeed even if not expected additional
    kwargs are passed.

    Note: this is a case when OPTIONS are requested on resource that is routed
        with URL template.
    """
    # note: creating request is optional here since we bypass whole falcon
    #       routing and dispatching procedure
    env = create_environ(method="OPTIONS")
    req = Request(env)   # noqa
    resource = Resource()

    resource.on_options(req, resp, additionnal_kwarg="foo")


def test_declarative_parameters(req, resp):
    class SomeResource(Resource):
        required_param = StringParam(details="some param", required=True)
        optional_param = StringParam(details="some param", required=False)

    # test existence of params property
    resource = SomeResource()
    assert 'required_param' in resource.params
    assert 'optional_param' in resource.params

    # test if params are describing themselves
    description = resource.describe(req, resp)
    assert 'required_param' in description['params']
    assert 'optional_param' in description['params']

    # test if there are basic keys in param description
    assert description['params']['required_param']['required'] is True
    assert description['params']['optional_param']['required'] is False


def test_parameter_inheritance():
    """
    Test that derrived classes inherit parameters and those can be overriden
    """
    class SomeResource(Resource):
        foo = StringParam(details="give me foo", required=False)
        bar = StringParam(details="give me bar", required=False)

    class DerrivedResource(SomeResource):
        # note: we toggle 'required' to check if was properly overriden
        bar = StringParam(details="overridden parameter", required=True)

    resource = DerrivedResource()

    # test both params are available
    assert 'foo' in resource.params
    assert 'bar' in resource.params

    # test 'bar' was overriden
    assert resource.params['bar'].required is True


def test_parameter_with_many_and_required():
    class SomeResource(Resource):
        foo = StringParam(details="give me foo", required=True, many=True)

    env = create_environ(query_string="foo=bar&foo=baz")
    resource = SomeResource()
    params = resource.require_params(Request(env))

    assert isinstance(params['foo'], Iterable)
    assert set(params['foo']) == {'bar', 'baz'}


def test_parameter_with_many_and_default(req):
    class SomeResource(Resource):
        foo = StringParam(details="give me foo", default='baz', many=True)

    resource = SomeResource()
    params = resource.require_params(req)

    assert isinstance(params['foo'], Iterable)
    assert params['foo'] == ['baz']

    env = create_environ(query_string="foo=bar")
    params = resource.require_params(Request(env))

    assert isinstance(params['foo'], Iterable)
    assert params['foo'] == ['bar']


def test_parameter_with_many_unspecified(req):
    class SomeResource(Resource):
        foo = StringParam(details="give me foo", many=True)

    resource = SomeResource()
    params = resource.require_params(req)

    assert 'foo' not in params


def test_parameter_value_errors_translated_to_http_errors(req, resp):
    class InvalidParam(BaseParam):
        def value(self, raw_value):
            raise ValueError("some error")

    class InvalidResource(TestResource):
        foo = InvalidParam("invalid", "having this will always raise error")

    resource = InvalidResource()

    # test GET without this param works fine
    resource.on_get(req, resp)

    # but with this parameter it should raise falcon.errors.HTTPBadRequest
    with pytest.raises(errors.HTTPBadRequest):
        req.params['foo'] = 'bar'
        resource.on_get(req, resp)


def test_default_parameters(req):
    class ResourceWithDefaults(Resource):
        foo = StringParam(details="foo with defaults", default="default")
        bar = StringParam(details="bar w/o default")

    resource = ResourceWithDefaults()
    params = resource.require_params(req)

    assert 'foo' in params
    assert params['foo'] == 'default'
    assert 'bar' not in params


def test_whole_serializer_validation_as_hhtp_bad_request(req):

    class TestSerializer(BaseSerializer):
        one = StringField("one different than two")
        two = StringField("two different than one")

        def validate(self, object_dict, partial=False):
            super().validate(object_dict, partial)
            # possible use case: kind of uniqueness relationship
            if object_dict['one'] == object_dict['two']:
                raise ValidationError("one must be different than two")

    class TestResource(Resource):
        serializer = TestSerializer()

    resource = TestResource()

    env = create_environ(
        body=json.dumps({'one': 'foo', 'two': 'foo'}),
        headers={'Content-Type': 'application/json'},
    )

    with pytest.raises(errors.HTTPBadRequest):
        resource.require_validated(Request(env))
