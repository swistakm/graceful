# -*- coding: utf-8 -*-
import base64
from falcon.testing import StartResponseMock, create_environ
import pytest

from falcon import API, HTTPUnauthorized
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
            *_, password_or_key = identifier
        else:
            password_or_key = identifier

        if password_or_key == self.password_or_key:
            return self.user


def simulate_request(api, path, **kwargs):
    srmock = StartResponseMock()
    result = api(create_environ(path=path, **kwargs), srmock)
    return result, srmock


@pytest.fixture(scope='module')
def testing_user():
    return {
        "username": "foo",
        "details": "bar",
        "password": "secretP4ssw0rd"
    }


@pytest.fixture(scope='module')
def auth_anonymous_app_route(testing_user):
    route = '/foo/'
    app = API(middleware=authentication.Anonymous(user=testing_user))
    app.add_route(route, ExampleResource())

    return app, route


@pytest.fixture(scope='module')
def auth_basic_app_route(testing_user):
    route = '/foo/'

    app = API(
        middleware=authentication.Basic(
            ExampleStorage(testing_user['password'], testing_user)
        )
    )
    app.add_route(route, ExampleResource())

    return app, route


def test_authentication_required_unauthorized(req, resp):
    resource = ExampleResource()

    with pytest.raises(HTTPUnauthorized):
        resource.on_get(req, resp)


def test_authentication_required_authorized(req, resp, testing_user):
    req.context['user'] = testing_user

    resource = ExampleResource()
    resource.on_get(req, resp)


def test_anonymous_auth(auth_anonymous_app_route):
    app, route = auth_anonymous_app_route

    result, srmock = simulate_request(app, route, method='GET')
    assert srmock.status == status_codes.HTTP_OK


def test_basic_auth(auth_basic_app_route, testing_user):
    app, route = auth_basic_app_route

    result, srmock = simulate_request(app, route, method='GET')
    assert srmock.status == status_codes.HTTP_UNAUTHORIZED

    result, srmock = simulate_request(
        app, route,
        headers={"Authorization": "Basic " + base64.b64encode(
            ":".join(
                [testing_user['username'], testing_user['password']]
            ).encode()
        ).decode()},
        method='GET',
    )
    assert srmock.status == status_codes.HTTP_OK
