# -*- coding: utf-8 -*-
import json
import base64
import binascii
import re
import abc

try:
    from functools import singledispatch
except ImportError:  # pragma: nocover
    # future: remove when dropping support for Python 3.3
    # compat: backport of singledispatch module introduced in Python 3.4
    from singledispatch import singledispatch

from falcon import HTTPMissingHeader, HTTPBadRequest


class BaseUserStorage(metaclass=abc.ABCMeta):
    """Base user storage class that defines required API for user storages.

    All built-in graceful authentication middleware classes expect user storage
    to have compatible API. Custom authentication middlewares do not need
    to use storages.

    .. versionadded:: 0.4.0
    """

    @abc.abstractmethod
    def get_user(
        self, identified_with, identifier, req, resp, resource, uri_kwargs
    ):
        """Get user from the storage.

        Args:
            identified_with (str): instance of the authentication middleware
                that provided the ``identifier`` value.
            identifier (str): string that identifies the user (it is specific
                for every authentication middleware implementation).
            req (falcon.Request): the request object.
            resp (falcon.Response): the response object.
            resource (object): the resource object.
            uri_kwargs (dict): keyword arguments from the URI template.

        Returns:
            the deserialized user object. Preferably a ``dict`` but it is
            application-specific.
        """
        raise NotImplementedError  # pragma: nocover

    @classmethod
    def __subclasshook__(cls, klass):
        """Verify implicit class interface."""
        if cls is BaseUserStorage:
            if any("get_user" in B.__dict__ for B in klass.__mro__):
                return True
        return NotImplemented


class DummyUserStorage(BaseUserStorage):
    """A dummy storage that never returns users or returns specified default.

    This storage is part of :any:`Anonymous` authentication middleware.
    It may also be useful for testing purposes or to disable specific
    authentication middlewares through app configuration.

    Args:
        user: User object to return. Defaults to ``None`` (will never
        authenticate).

    .. versionadded:: 0.4.0
    """

    def __init__(self, user=None):
        """Initialize dummy storage."""
        self.user = user

    def get_user(
        self, identified_with, identifier, req, resp, resource, uri_kwargs
    ):
        """Return default user object."""
        return self.user


class IPRangeWhitelistStorage(BaseUserStorage):
    """Simple storage dedicated for :any:`XForwardedFor` authentication.

    This storage expects that authentication middleware return client address
    from its ``identify()`` method. For example usage see :any:`XForwardedFor`.
    Because it is IP range whitelist this storage it cannot distinguish
    different users' IP and always returns default user object. If you want to
    identify different users by their IP see :any:`KeyValueUserStorage`.

    Args:
        ip_range: Any object that supports ``in`` operator (i.e. implements the
            ``__cointains__`` method). The ``__contains__`` method should
            return ``True`` if identifier falls into specified whitelist.
            Tip: use ``iptools``.
        user: Default user object to return on successful authentication.

    .. versionadded:: 0.4.0
    """

    def __init__(self, ip_range, user):
        """Initialize IP whitelist storage."""
        self.ip_range = ip_range
        self.user = user

    def get_user(
        self, identified_with, identifier, req, resp, resource, uri_kwargs
    ):
        """Return default user object.

        .. note::
            This implementation expects that ``identifier`` is an user address.
        """
        if identifier in self.ip_range:
            return self.user


class KeyValueUserStorage(BaseUserStorage):
    """Basic user storage using any key-value store as authentication backend.

    Client identities are stored as string under keys matching following
    template::

        <key_prefix>:<identified_with>:<identifier>

    Where:

    * ``<key_prefix>`` is the configured key prefix (same as the initialization
      argument),
    * ``<identified_with>`` is the name of authentication middleware that
      provided user identifier,
    * ``<identifier>`` is the identifier object that identifies the user.

    Note that this key scheme will work only for middlewares that return
    identifiers as single string objects. Also the ``<identifier>`` part
    of key template is a plain text value of without any hashing algorithm
    applied. It may not be secure enough to store user secrets that way.

    If you want to use this storage with middleware that uses more complex
    identifier format/objects (e.g. the :any:`Basic` class) you will have
    to register own identifier format in the :any:`hash_identifier` method.
    For details see the :any:`hash_identifier` method docstring or the
    :ref:`practical example <auth-practical-example>` section of the
    documentation.

    Args:
        kv_store: Key-value store client instance (e.g. Redis client object).
            The ``kv_store`` must provide at least two methods: ``get(key)``
            and ``set(key, value)``. The arguments and return values of these
            methods must be strings.
        key_prefix: key prefix used to store client identities.
        serialization: serialization object/module that uses the
            ``dumps()``/``loads()`` protocol. Defaults to ``json``.

    .. versionadded:: 0.4.0
    """

    def __init__(self, kv_store, key_prefix='users', serialization=None):
        """Initialize kv_store user storage."""
        self.kv_store = kv_store
        self.key_prefix = key_prefix
        self.serialization = serialization or json

    def _get_storage_key(self, identified_with, identifier):
        """Get key string for given user identifier in consistent manner."""
        return ':'.join((
            self.key_prefix, identified_with.name,
            self.hash_identifier(identified_with, identifier),
        ))

    @staticmethod
    @singledispatch
    def hash_identifier(identified_with, identifier):
        """Create hash from identifier to be used as a part of user lookup.

        This method is a ``singledispatch`` function. It allows to register
        new implementations for specific authentication middleware classes:

        .. code-block:: python

            from hashlib import sha1

            from graceful.authentication import KeyValueUserStorage, Basic

            @KeyValueUserStorage.hash_identifier.register(Basic)
            def _(identified_with, identifier):
                return ":".join((
                    identifier[0],
                    sha1(identifier[1].encode()).hexdigest(),
                ))

        Args:
            identified_with (str): name of the authentication middleware used
                to identify the user.
            identifier (str): user identifier string

        Return:
            str: hashed identifier string
        """
        if isinstance(identifier, str):
            return identifier
        else:
            raise TypeError(
                "User storage does not support this kind of identifier"
            )

    def get_user(
        self, identified_with, identifier, req, resp, resource, uri_kwargs
    ):
        """Get user object for given identifier.

        Args:
            identified_with (object): authentication middleware used
                to identify the user.
            identifier: middleware specifix user identifier (string or tuple
                in case of all built in authentication middleware classes).

        Returns:
            dict: user object stored in Redis if it exists, otherwise ``None``
        """
        stored_value = self.kv_store.get(
            self._get_storage_key(identified_with, identifier)
        )
        if stored_value is not None:
            user = self.serialization.loads(stored_value.decode())
        else:
            user = None

        return user

    def register(self, identified_with, identifier, user):
        """Register new key for given client identifier.

        This is only a helper method that allows to register new
        user objects for client identities (keys, tokens, addresses etc.).

        Args:
            identified_with (object): authentication middleware used
                to identify the user.
            identifier (str): user identifier.
            user (str): user object to be stored in the backend.
        """
        self.kv_store.set(
            self._get_storage_key(identified_with, identifier),
            self.serialization.dumps(user).encode(),
        )


class BaseAuthenticationMiddleware:
    """Base class for all authentication middleware classes.

    Args:
        user_storage (BaseUserStorage): a storage object used to retrieve
            user object using their identifier lookup.
        name (str): custom name of the authentication middleware useful
            for handling custom user storage backends. Defaults to middleware
            class name.

    .. versionadded:: 0.4.0
    """

    #: challenge returned in WWW-Authenticate header on non authorized
    #: requests.
    challenge = None

    #: defines if Authentication middleware requires valid storage
    #: object to identify users
    only_with_storage = False

    def __init__(self, user_storage=None, name=None):
        """Initialize authentication middleware."""
        self.user_storage = user_storage
        self.name = (
            name if name else self.__class__.__name__
        )

        if (
            self.only_with_storage and
            not isinstance(self.user_storage, BaseUserStorage)
        ):
            raise ValueError(
                "{} authentication middleware requires valid storage. Got {}."
                "".format(self.__class__.__name__, self.user_storage)
            )

    def process_resource(self, req, resp, resource, uri_kwargs=None):
        """Process resource after routing to it.

        This is basic falcon middleware handler.

        Args:
            req (falcon.Request): request object
            resp (falcon.Response): response object
            resource (object): resource object matched by falcon router
            uri_kwargs (dict): additional keyword argument from uri template.
                For ``falcon<1.0.0`` this is always ``None``
        """
        if 'user' in req.context:
            return

        identifier = self.identify(req, resp, resource, uri_kwargs)
        user = self.try_storage(identifier, req, resp, resource, uri_kwargs)

        if user is not None:
            req.context['user'] = user

        # if did not succeed then we need to add this to list of available
        # challenges.
        elif self.challenge is not None:
            req.context.setdefault(
                'challenges', list()
            ).append(self.challenge)

    def identify(self, req, resp, resource, uri_kwargs):
        """Identify the user that made the request.

        Args:
            req (falcon.Request): request object
            resp (falcon.Response): response object
            resource (object): resource object matched by falcon router
            uri_kwargs (dict): additional keyword argument from uri template.
                For ``falcon<1.0.0`` this is always ``None``

        Returns:
            object: a user object (preferably a dictionary).
        """
        raise NotImplementedError  # pragma: nocover

    def try_storage(self, identifier, req, resp, resource, uri_kwargs):
        """Try to find user in configured user storage object.

        Args:
            identifier: User identifier.

        Returns:
            user object.
        """
        if identifier is None:
            user = None

        # note: if user_storage is defined, always use it in order to
        #       authenticate user.
        elif self.user_storage is not None:
            user = self.user_storage.get_user(
                self, identifier, req, resp, resource, uri_kwargs
            )

        # note: some authentication middleware classes may not require
        #       to be initialized with their own user_storage. In such
        #       case this will always authenticate with "syntetic user"
        #       if there is a valid indentity.
        elif self.user_storage is None and not self.only_with_storage:
            user = {
                'identified_with': self,
                'identifier': identifier
            }

        else:  # pragma: nocover
            # note: this should not happen if the base class is properly
            #       initialized. Still, user can skip super().__init__() call.
            user = None

        return user


class Basic(BaseAuthenticationMiddleware):
    """Authenticate user with Basic auth as specified by `RFC 7617`_.

    Token authentication takes form of ``Authorization`` header in the
    following form::

        Authorization: Basic <credentials>

    Whre `<credentials>` is base64 encoded username and password separated by
    single colon charactes (refer to official RFC). Usernames must not contain
    colon characters!

    If client fails to authenticate on protected endpoint the response will
    include following challenge::

        WWW-Authenticate: Basic realm="<realm>"

    Where ``<realm>`` is the value of configured authentication realm.

    This middleware **must** be configured with ``user_storage`` that provides
    access to database of client API keys and their identities. Additionally.
    the ``identifier`` received by user storage in the ``get_user()`` method
    is a decoded ``<username>:<password>`` string. If you need to apply any
    hash function before hitting database in your user storage handler, you
    should split it using followitg code::

        username, _, password = identifier.partition(":")

    Args:
        realm (str): name of the protected realm. This can be only alphanumeric
            string with spaces (see: the ``REALM_RE`` pattern).
        user_storage (BaseUserStorage): a storage object used to retrieve
            user object using their identifier lookup.
        name (str): custom name of the authentication middleware useful
            for handling custom user storage backends. Defaults to middleware
            class name.

    .. versionadded:: 0.4.0

    .. _RFC 7617: https://tools.ietf.org/html/rfc7616
    """

    only_with_storage = True

    #: regular expression used to validate configured realm
    REALM_RE = re.compile(r"^[\w ]+$")

    def __init__(self, user_storage=None, name=None, realm="api"):
        """Initialize middleware and validate realm string."""
        if not self.REALM_RE.match(realm):
            raise ValueError(
                "realm argument should match '{}' regular expression"
                "".format(self.REALM_RE.pattern)
            )

        self.challenge = "Basic realm={}".format(realm)
        super(Basic, self).__init__(user_storage, name)

    def identify(self, req, resp, resource, uri_kwargs):
        """Identify user using Authenticate header with Basic auth."""
        header = req.get_header("Authorization", False)
        auth = header.split(" ") if header else None

        if auth is None or auth[0].lower() != 'basic':
            return None

        if len(auth) != 2:
            raise HTTPBadRequest(
                "Invalid Authorization header",
                "The Authorization header for Basic auth should be in form:\n"
                "Authorization: Basic <base64-user-pass>"
            )

        user_pass = auth[1]

        try:
            decoded = base64.b64decode(user_pass).decode()

        except (TypeError, UnicodeDecodeError, binascii.Error):
            raise HTTPBadRequest(
                "Invalid Authorization header",
                "Credentials for Basic auth not correctly base64 encoded."
            )

        username, _, password = decoded.partition(":")
        return username, password


class XAPIKey(BaseAuthenticationMiddleware):
    """Authenticate user with ``X-Api-Key`` header.

    The X-Api-Key authentication takes a form of ``X-Api-Key`` header in the
    following form::

        X-Api-Key: <key_value>

    Where ``<key_value>`` is a secret string known to both client and server.
    Example of valid header::

        X-Api-Key: 6fa459ea-ee8a-3ca4-894e-db77e160355e

    If client fails to authenticate on protected endpoint the response will
    include following challenge::

        WWW-Authenticate: X-Api-Key

    .. note::
        This method functionally equivalent to :any:`Token` and is included
        only to ease migration of old applications that could use such
        authentication method in past. If you're building new API and require
        only simple token-based authentication you should prefere
        :any:`Token` middleware.

    This middleware **must** be configured with ``user_storage`` that provides
    access to database of client API keys and their identities.

    .. versionadded:: 0.4.0
    """

    challenge = 'X-Api-Key'
    only_with_storage = True

    def identify(self, req, resp, resource, uri_kwargs):
        """Initialize X-Api-Key authentication middleware."""
        try:
            return req.get_header('X-Api-Key', True)
        except (KeyError, HTTPMissingHeader):
            pass


class Token(BaseAuthenticationMiddleware):
    """Authenticate user using Token authentication.

    Token authentication takes form of ``Authorization`` header::

        Authorization: Token <token_value>

    Where ``<token_value>`` is a secret string known to both client and server.
    Example of valid header::

        Authorization: Token 6fa459ea-ee8a-3ca4-894e-db77e160355e

    If client fails to authenticate on protected endpoint the response will
    include following challenge::

        WWW-Authenticate: Token

    This middleware **must** be configured with ``user_storage`` that provides
    access to database of client tokens and their identities.

    .. versionadded:: 0.4.0
    """

    challenge = 'Token'
    only_with_storage = True

    def identify(self, req, resp, resource, uri_kwargs):
        """Identify user using Authenticate header with Token auth."""
        header = req.get_header('Authorization', False)
        auth = header.split(' ') if header else None

        if auth is None or auth[0].lower() != 'token':
            return None

        if len(auth) != 2:
            raise HTTPBadRequest(
                "Invalid Authorization header",
                "The Authorization header for Token auth should be in form:\n"
                "Authorization: Token <token_value>"
            )

        return auth[1]


class XForwardedFor(BaseAuthenticationMiddleware):
    """Authenticate user with ``X-Forwarded-For`` header or remote address.

    Args:
        remote_address_fallback (bool): Use fallback to ``REMOTE_ADDR`` value
            from WSGI environment dictionary if ``X-Forwarded-For`` header is
            not available. Defaults to ``False``.


    This authentication middleware is usually used with the
    :any:`IPRangeWhitelistStorage` e.g:


    .. code-block:: python

        from iptools import IPRangeList
        import falcon

        from graceful import authentication

        IP_WHITELIST = IpRangeList(
            '127.0.0.1',
            # ...
        )

        auth_middleware = authentication.XForwardedFor(
            user_storage=authentication.IPWRangehitelistStorage(
                IP_WHITELIST, user={"username": "internal"}
            )
        )

        api = application = falcon.API(middleware=[auth_middleware])

    .. note::
        Using this middleware class is **highly unrecommended** if you
        are not able to ensure that contents of ``X-Forwarded-For`` header
        can be trusted. This requires proper reverse proxy and network
        configuration. It is also recommended to at least use the static
        :any:`IPRangeWhitelistStorage` as the user storage.

    .. versionadded:: 0.4.0
    """

    challenge = None
    only_with_storage = False

    def __init__(
        self, user_storage=None, name=None, remote_address_fallback=False
    ):
        """Initialize middleware and set default arguments."""
        super().__init__(user_storage, name)
        self.remote_address_fallback = remote_address_fallback

    def _get_client_address(self, req):
        """Get address from ``X-Forwarded-For`` header or use remote address.

        Remote address is used if the ``X-Forwarded-For`` header is not
        available. Note that this may not be safe to depend on both without
        proper authorization backend.

        Args:
            req (falcon.Request): falcon.Request object.

        Returns:
            str: client address.
        """
        try:
            forwarded_for = req.get_header('X-Forwarded-For', True)
            return forwarded_for.split(',')[0].strip()
        except (KeyError, HTTPMissingHeader):
            return (
                req.env.get('REMOTE_ADDR') if self.remote_address_fallback
                else None
            )

    def identify(self, req, resp, resource, uri_kwargs):
        """Identify client using his address."""
        return self._get_client_address(req)


class Anonymous(BaseAuthenticationMiddleware):
    """Dummy authentication middleware that authenticates every request.

    It makes every every request authenticated with default value of
    anonymous user. This authentication middleware may be used in order
    to simplify custom authorization code since it will ensure that
    every request context will have the ``'user'`` variable defined.

    .. note::
        This middleware will always add the default user to the request
        context if no other previous authentication middleware resolved.
        So if this middleware is used it makes no sense to:

        * Use the :any:`authentication_required` decorator.
        * Define any other authentication middleware after this one.

    Args:
        user: Default anonymous user object.

    .. versionadded:: 0.4.0
    """

    challenge = None
    only_with_storage = True

    def __init__(self, user):
        """Initialize anonymous authentication middleware."""
        # note: DummyUserStorage allows to always return the same user
        #       object that was passed as initialization value
        super().__init__(user_storage=DummyUserStorage(user))

    def identify(self, req, resp, resource, uri_kwargs):
        """Identify user with a dummy sentinel value."""
        # note: this is just a sentinel value to trigger successful
        #       lookup in the dummy user storage
        return ...
