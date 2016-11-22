# -*- coding: utf-8 -*-
import base64
import pytest

from falcon import testing, API, HTTPUnauthorized
from falcon import status_codes

from graceful.resources.base import BaseResource
from graceful import authentication
from graceful import authorization


@authorization.authentication_required
class ExampleResource(BaseResource, with_context=True):
    def on_get(self, req, resp, **kwargs):
        assert 'user' in req.context


class ExampleStorage(authentication.BaseUserStorage):
    def __init__(self, password_or_key, user):
        self.password_or_key = password_or_key
        self.user = user

    def get_user(
        self, identified_with, identifier, req, resp, resource, uri_kwargs
    ):
        if isinstance(identified_with, authentication.Basic):
            import ipdb; ipdb.set_trace()
            *_, password_or_key = identifier.partition(":")
        else:
            password_or_key = identifier

        if password_or_key == self.password_or_key:
            return self.user


@pytest.fixture(scope='module')
def testing_user():
    return {
        "username": "foo",
        "password": "bar",
    }


@pytest.fixture(scope='module')
def auth_anonymous_client(testing_user):
    route = '/foo/'
    app = API(middleware=authentication.Anonymous(user=testing_user))
    app.add_route(route, ExampleResource())

    test_client = testing.TestClient(app)
    test_client.user = testing_user
    test_client.route = route
    return test_client


@pytest.fixture(scope='module')
def auth_basic_client(testing_user):
    route = '/foo/'

    password = "secretP4ssw0rd"
    username = "foo_bar"

    app = API(
        middleware=authentication.Basic(
            ExampleStorage(password, testing_user)
        )
    )
    app.add_route(route, ExampleResource())

    test_client = testing.TestClient(app)

    test_client.user = testing_user
    test_client.route = route
    test_client.password = password
    test_client.username = username

    return test_client


def test_authentication_required_unauthorized(req, resp):
    resource = ExampleResource()

    with pytest.raises(HTTPUnauthorized):
        resource.on_get(req, resp)


def test_authentication_required_authorized(req, resp, testing_user):
    req.context['user'] = testing_user

    resource = ExampleResource()
    resource.on_get(req, resp)


def test_anonymous_auth(auth_anonymous_client):
    result = auth_anonymous_client.simulate_get(auth_anonymous_client.route)
    assert result.status == status_codes.HTTP_OK


def test_basic_auth(auth_basic_client):
    result = auth_basic_client.simulate_get(auth_basic_client.route)
    assert result.status == status_codes.HTTP_UNAUTHORIZED

    result = auth_basic_client.simulate_get(
        auth_basic_client.route,
        headers={"Authorization": "Basic " + base64.b64encode(
            ":".join(
                [auth_basic_client.username, auth_basic_client.password]
            ).encode()
        ).decode()}

    )
    assert result.status == status_codes.HTTP_UNAUTHORIZED
