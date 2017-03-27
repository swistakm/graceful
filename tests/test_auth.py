# -*- coding: utf-8 -*-
import base64
import pytest
import hashlib

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


class ExampleKVUserStorage(authentication.KeyValueUserStorage):
    class SimpleKVStore(dict):
        def set(self, key, value):
            self[key] = value

    def __init__(self, data=None):
        super().__init__(self.SimpleKVStore(data or {}))

    def clear(self):
        self.kv_store.clear()


@ExampleKVUserStorage.hash_identifier.register(authentication.Basic)
def _(identified_with, identifier):
    return ":".join([
        identifier[0],
        hashlib.sha1(identifier[1].encode()).hexdigest()
    ])


def test_default_kv_hashes_only_strings():
    with pytest.raises(TypeError):
        ExampleKVUserStorage.hash_identifier(None, [1, 2, 3, 4])


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
        "password": "secretP4ssw0rd",
        "allowed_ip": "127.100.100.1",
        "allowed_remote": "127.0.0.1",
        "token": "s3cr3t70ken",
        'allowed_ip_range': ['127.100.100.1'],
    }
    ident_keys = ['password']
    auth_storage = ExampleKVUserStorage()
    auth_middleware = [authentication.Anonymous(user)]

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

        self.auth_storage.clear()

        identity = [self.user[key] for key in self.ident_keys]

        self.auth_storage.register(
            self.auth_middleware[0],
            identity[0] if len(identity) == 1 else identity,
            self.user
        )

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
    auth_middleware = [authentication.Anonymous(...)]

    def get_authorized_headers(self):
        return {}

    def get_unauthorized_headers(self):
        # note: Anonymous always authenticates the user.
        raise self.SkipTest

    def get_invalid_headers(self):
        # note: it is not possible to have invalid header for this auth.
        raise self.SkipTest


class BasicAuthTestCase(AuthTestsMixin, TestBase):
    auth_middleware = [authentication.Basic(AuthTestsMixin.auth_storage)]
    ident_keys = ['username', 'password']

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
    auth_middleware = [authentication.Token(AuthTestsMixin.auth_storage)]
    ident_keys = ['token']

    def get_authorized_headers(self):
        return {"Authorization": "Token " + self.user['token']}

    def get_invalid_headers(self):
        return {"Authorization": "Token Token Token"}


class XAPIKeyAuthTestCase(AuthTestsMixin, TestBase):
    auth_middleware = [authentication.XAPIKey(AuthTestsMixin.auth_storage)]
    ident_keys = ['token']

    def get_authorized_headers(self):
        return {"X-Api-Key": self.user['token']}

    def get_invalid_headers(self):
        # note: it is not possible to have invalid header for this auth.
        raise self.SkipTest


class XForwardedForAuthTestCase(AuthTestsMixin, TestBase):
    auth_middleware = [
        authentication.XForwardedFor(AuthTestsMixin.auth_storage)
    ]
    ident_keys = ['allowed_ip']

    def get_authorized_headers(self):
        return {"X-Forwarded-For": self.user['allowed_ip']}

    def get_invalid_headers(self):
        # note: it is not possible to have invalid header for this auth.
        raise self.SkipTest


class XForwardedForWithoutStorageAuthTestCase(AuthTestsMixin, TestBase):
    auth_middleware = [authentication.XForwardedFor()]
    ident_keys = ['allowed_ip']

    def get_authorized_headers(self):
        return {"X-Forwarded-For": self.user['allowed_ip']}

    def get_invalid_headers(self):
        # note: it is not possible to have invalid header for this auth.
        raise self.SkipTest


class XForwardedForWithFallbackAuthTestCase(AuthTestsMixin, TestBase):
    auth_middleware = [
        authentication.XForwardedFor(remote_address_fallback=True)
    ]
    ident_keys = ['allowed_remote']

    def get_authorized_headers(self):
        return {}

    def get_unauthorized_headers(self):
        raise self.SkipTest

    def get_invalid_headers(self):
        # note: it is not possible to have invalid header for this auth.
        raise self.SkipTest


class IPRangeXForwardedForAuthTestCase(AuthTestsMixin, TestBase):
    class IPRangeWhitelistStorage(authentication.IPRangeWhitelistStorage):
        """Test compatible implementation of IPRangeWhitelistStorage.

        This implementation simply extends the base class with
        tests-compatible ``register()`` and ``clear()`` methods.
        """

        def register(self, identified_with, identity, user):
            self.ip_range = identity
            self.user = user

        def clear(self):
            self.ip_range = []
            self.user = None

    auth_storage = IPRangeWhitelistStorage([], None)
    auth_middleware = [
        authentication.XForwardedFor(auth_storage)
    ]
    ident_keys = ['allowed_ip_range']

    def get_authorized_headers(self):
        return {'X-Forwarded-For': self.user['allowed_ip_range'][0]}

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
    ident_keys = ["token"]

    def get_unauthorized_headers(self):
        # note: Anonymous will always authenticate the user as a fallback auth
        raise self.SkipTest

    def get_invalid_headers(self):
        # this is invalid header for basic authentication
        return {"Authorization": "Token Basic Basic"}

    def get_authorized_headers(self):
        return {"Authorization": "Token " + self.user['password']}
