# -*- coding: utf-8 -*-
import base64

import pytest

from falcon.testing import TestBase
from falcon import API
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


def test_invalid_basic_auth_realm():
    with pytest.raises(ValueError):
        authentication.Basic(realm="Impro=per realm%%% &")


@pytest.mark.parametrize(
    "auth_class", [
        authentication.Basic,
        authentication.Token,
        authentication.XAPIKey,
    ]
)
def test_auth_requires_storage(auth_class):
    with pytest.raises(ValueError):
        auth_class()


class AuthTestsMixin:
    """ Test mixin that defines common routine for testing auth classes.
    """

    class SkipTest(Exception):
        """Raised when given tests is marked to be skipped

        Note: we use this exception instead of self.skipTest() method because
        this has slightly different semantics. We simply don't want to report
        these tests as skipped.
        """

    route = '/foo/'
    user = {
        "username": "foo",
        "details": "bar",
        "password": "secretP4ssw0rd"
    }
    auth_storage = ExampleStorage(user['password'], user)
    auth_middleware = authentication.Anonymous(user)

    def get_authorized_headers(self):
        raise NotImplementedError

    def get_invalid_headers(self):
        raise NotImplementedError

    def get_unauthorized_headers(self):
        return {}

    def setUp(self):
        super().setUp()
        self.api = API(middleware=self.auth_middleware)
        self.api.add_route(self.route, ExampleResource())

    def test_unauthorized(self):
        try:
            self.simulate_request(
                self.route, decode='utf-8', method='GET',
                headers=self.get_unauthorized_headers()
            )
            assert self.srmock.status == status_codes.HTTP_UNAUTHORIZED
        except self.SkipTest:
            pass

    def test_authorized(self):
        try:
            self.simulate_request(
                self.route, decode='utf-8', method='GET',
                headers=self.get_authorized_headers()
            )
            assert self.srmock.status == status_codes.HTTP_OK
        except self.SkipTest:
            pass

    def test_bad_request(self):
        try:
            maybe_multiple_headers_sets = self.get_invalid_headers()

            if isinstance(maybe_multiple_headers_sets, tuple):
                header_sets = maybe_multiple_headers_sets

            else:
                header_sets = (maybe_multiple_headers_sets,)

            for headers in header_sets:
                self.simulate_request(
                    self.route, decode='utf-8', method='GET',
                    headers=headers
                )
                assert self.srmock.status == status_codes.HTTP_BAD_REQUEST
        except self.SkipTest:
            pass


class AnonymousAuthTestCase(AuthTestsMixin, TestBase):
    auth_middleware = authentication.Anonymous(...)

    def get_authorized_headers(self):
        return {}

    def get_unauthorized_headers(self):
        # note: Anonymous always authenticates the user.
        raise self.SkipTest

    def get_invalid_headers(self):
        # note: it is not possible to have invalid header for this auth.
        raise self.SkipTest


class BasicAuthTestCase(AuthTestsMixin, TestBase):
    auth_middleware = authentication.Basic(AuthTestsMixin.auth_storage)

    def get_authorized_headers(self):
        return {
            "Authorization":
                "Basic " + base64.b64encode(
                    ":".join(
                        [self.user['username'], self.user['password']]
                    ).encode()
                ).decode()
        }

    def get_invalid_headers(self):
        return (
            # to many header tokens
            {"Authorization": "Basic Basic Basic"},
            # non base64 decoded
            {"Authorization": "Basic nonbase64decoded"}
        )


class TokenAuthTestCase(AuthTestsMixin, TestBase):
    auth_middleware = authentication.Token(AuthTestsMixin.auth_storage)

    def get_authorized_headers(self):
        return {"Authorization": "Token " + self.user['password']}

    def get_invalid_headers(self):
        return {"Authorization": "Token Token Token"}


class XAPIKeyAuthTestCase(AuthTestsMixin, TestBase):
    auth_middleware = authentication.XAPIKey(AuthTestsMixin.auth_storage)

    def get_authorized_headers(self):
        return {"X-Api-Key": self.user['password']}

    def get_invalid_headers(self):
        # note: it is not possible to have invalid header for this auth.
        raise self.SkipTest


class XForwardedForAuthTestCase(AuthTestsMixin, TestBase):
    auth_storage = authentication.IPWhitelistStorage(["127.100.100.1"], ...)
    auth_middleware = authentication.XForwardedFor(auth_storage)

    def get_authorized_headers(self):
        return {"X-Forwarded-For": "127.100.100.1"}

    def get_invalid_headers(self):
        # note: it is not possible to have invalid header for this auth.
        raise self.SkipTest


class XForwardedForWithoutStorageAuthTestCase(AuthTestsMixin, TestBase):
    auth_middleware = authentication.XForwardedFor()

    def get_authorized_headers(self):
        return {"X-Forwarded-For": "127.0.0.1"}

    def get_invalid_headers(self):
        # note: it is not possible to have invalid header for this auth.
        raise self.SkipTest


class XForwardedForWithFallbackAuthTestCase(AuthTestsMixin, TestBase):
    auth_middleware = authentication.XForwardedFor(
        remote_address_fallback=True
    )

    def get_authorized_headers(self):
        return {}

    def get_unauthorized_headers(self):
        raise self.SkipTest

    def get_invalid_headers(self):
        # note: it is not possible to have invalid header for this auth.
        raise self.SkipTest


class MultipleAuthTestCase(AuthTestsMixin, TestBase):
    auth_middleware = [
        authentication.Token(AuthTestsMixin.auth_storage),
        authentication.Anonymous(...),
        authentication.Basic(AuthTestsMixin.auth_storage),
    ]

    def get_unauthorized_headers(self):
        # note: Anonymous will always authenticate the user as a fallback auth
        raise self.SkipTest

    def get_invalid_headers(self):
        # this is invalid header for basic authentication
        return {"Authorization": "Token Basic Basic"}

    def get_authorized_headers(self):
        return {"Authorization": "Token " + self.user['password']}
