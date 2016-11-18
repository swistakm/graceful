# -*- coding: utf-8 -*-
import json

from falcon import HTTPMissingHeader


class BaseUserStorage:
    """Base user storage class that defines required API for user storages.

    All built in graceful authentication middleware classes expect user storage
    to have compatible API. Custom authentication middlewares do not need
    to use storages and even they use any they do not neet to have compatible
    interfaces.
    """

    def get_user(
        self, identified_with, identity, req, resp, resource, uri_kwargs
    ):
        """Get user from the storage.

        Args:
            identified_with (str): name of the authentication middleware used
                to identify the user.
            identify (str): string that identifies the user (it is specific
                for every authentication middleware implementation).
            req (falcon.Request): the request object.
            resp (falcon.Response): the response object.
            resource (object): the resource object.
            uri_kwargs (dict): keyword arguments from the URI template.

        Returns:
            the deserialized user object. Preferably a ``dict`` but it is
            application-specific.
        """
        raise NotImplementedError


class DummyUserStorage(BaseUserStorage):
    """A dummy storage that always returns no users or specified default.

    This storage is part of :any:`Anonymous` authentication middleware
    but also may be useful for testing or disabling specific authentication
    middlewares through app configuration.

    Args:
        user: user to return. Defaults to ``None`` (will never authenticate).
    """

    def __init__(self, user=None):
        """Initialize dummy storage."""
        self.user = user

    def get_user(
        self, identified_with, identity, req, resp, resource, uri_kwargs
    ):
        """Return default user object."""
        return self.user


class IPWhitelistStorage(BaseUserStorage):
    """Simple storage dedicated for :any:`XForwardedFor` authentication.

    This storage expects that is used with authentication middleware that
    returns client address from its ``identify()`` method.

    Args:
        ip_range: any object that supports ``in`` operator in order to check
            if identity falls into specified whitelist. Tip: use ``iptools``.
        user: default user to return on successful authentication.
    """

    def __init__(self, ip_range, user):
        """Initialize IP whitelist storage."""
        self.ip_range = ip_range
        self.user = user

    def get_user(
        self, identified_with, identity, req, resp, resource, uri_kwargs
    ):
        """Return default user object.

        .. note::
            This implementation expects that ``identity`` is an user address.
        """
        if identity in self.ip_range:
            return self.user


class RedisUserStorage(BaseUserStorage):
    """Basic API key identity storage in Redis.

    Client identities are stored as string under keys mathing following
    template:

        <key_prefix>:<identified_with>:<identity>

    Args:
        redis: Redis client instance
        key_prefix: key prefix used to store client identities.
        serialization: serialization object/module that uses the
            ``dumps()``/``loads()`` protocol. Defaults to ``json``.
    """

    def __init__(self, redis, key_prefix='users', serialization=json):
        """Initialize redis user storage."""
        self.redis = redis
        self.key_prefix = key_prefix
        self.serialization = serialization

    def _get_storage_key(self, identified_with, identity):
        """Consistently get Redis key name of identity string for api key.

        Args:
            identified_with (str): name of the authentication middleware used
                to identify the user.
            identity (str): user identity string

        Return:
            str: user object key name
        """
        return ':'.join((self.key_prefix, identified_with, identity))

    def get_user(
        self, identified_with, identity, req, resp, resource, uri_kwargs
    ):
        """Get identity string for given API key.

        Args:
            identified_with (str): name of the authentication middleware used
                to identify the user.
            identity (str): user identity.

        Returns:
            dict: user objet stored in Redis if it exists, otherwise ``None``
        """
        stored_value = self.redis.get(
            self._get_storage_key(identified_with, identity)
        )
        if stored_value is not None:
            user = self.serialization.loads(stored_value.decode())
        else:
            user = None

        return user

    def register(self, identified_with, identity, user):
        """Register new key for given client identity.

        This is only a helper method that allows to register new
        user objects for client identities (keys, tokens, addresses etc.).

        Args:
            identified_with (str): name of the authentication middleware used
                to identify the user.
            identity (str): user identity.
            user (str): user object to be stored in the backend.
        """
        self.redis.set(
            self._get_storage_key(identified_with, identity),
            self.serialization.dumps(user).encode(),
        )


class BaseAuthenticationMiddleware:
    """Base class for all authentication middleware classes.

    Args:
        user_storage (BaseUserStorage): a storage object used to retrieve
            user object using their identity lookup.
        name (str): custom name of the authentication middleware useful
            for handling custom user storage backends. Defaults to middleware
            class name.
    """

    #: challenge returned in WWW-Authenticate header on non authorized
    #: requests.
    challenge = None

    #: defines if Authentication middleware requires valid storage
    #: object to identify users
    storage_required = False

    def __init__(self, user_storage=None, name=None):
        """Initialize authentication middleware."""
        self.user_storage = user_storage
        self.name = (
            name if name else self.__class__.__name__
        )

        if self.storage_required and self.user_storage is None:
            raise ValueError(
                "{} authentication middleware requires valid storage"
                "".format(self.__class__.__name__)
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

        identity = self.identify(req, resp, resource, uri_kwargs)
        user = self.try_storage(identity, req, resp, resource, uri_kwargs)

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
        raise NotImplementedError

    def try_storage(self, identity, req, resp, resource, uri_kwargs):
        """Try to find user in configured user storage object.

        Args:
            identity (str): user identity.

        Returns:
            user object
        """
        # note: if user_storage is defined, always use it in order to
        #       authenticate user.
        if self.user_storage is not None:
            user = self.user_storage.get_user(
                self.name, identity, req, resp, resource, uri_kwargs
            )

        # note: some authentication middleware classes may not require
        #       to be initialized with their own user_storage. In such
        #       case this will always authenticate with "syntetic user"
        #       if there is valid indentity.
        # todo: consider renaming "storage_required" to something else
        elif self.user_storage is None and not self.storage_required:
            user = {
                'identified_with': self.name,
                'identity': identity
            }

        else:
            user = None

        return user


class XAPIKey(BaseAuthenticationMiddleware):
    """Authenticate user with ``X-Api-Key`` header.

    This middleware must be configured with ``user_storage`` that provides
    access to database of client API keys and their identities.
    """

    challenge = 'X-Api-Key'
    storage_required = True

    def identify(self, req, resp, resource, uri_kwargs):
        """Initialize X-Api-Key authentication middleware."""
        try:
            return req.get_header('X-Api-Key', True)
        except (KeyError, HTTPMissingHeader):
            pass


class Token(BaseAuthenticationMiddleware):
    """Authenticate user using Token authentication.

    .. todo:: documentation and RFC link.
    """

    challenge = 'Token'
    storage_required = True

    def identify(self, req, resp, resource, uri_kwargs):
        """Identify user using Authenticate header with Token."""
        try:
            # todo: verify correctness
            header = req.get_header('Authenticate', True)
            parts = header.split(' ')

            if len(parts) == 2 and parts[0] == 'Token':
                return parts[1]

        except (KeyError, HTTPMissingHeader):
            pass


class XForwardedFor(BaseAuthenticationMiddleware):
    """Authenticate user with ``X-Forwarded-For`` header or remote address.

    .. note::
        Using this middleware class is **highly unrecommended** if you
        are not able to ensure that contents of ``X-Forwarded-For`` header
        can be trusted. This requires proper reverse proxy and network
        configuration. It is also recommended to at least use the static
        :any:`IPWhitelistStorage` as the user storage.
    """

    challenge = None
    storage_required = False

    @staticmethod
    def _get_client_address(req):
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
            # in case our worker is behind reverse proxy
            forwarded_for = req.get_header('X-Forwarded-For', True)
            return forwarded_for.split(',')[0].strip()
        except (KeyError, HTTPMissingHeader):  # pragma: nocover
            return req.env.get('REMOTE_ADDR')

    def identify(self, req, resp, resource, uri_kwargs):
        """Identify client using his address."""
        return self._get_client_address(req)


class Anonymous(BaseAuthenticationMiddleware):
    """Dummy authentication middleware that authenticates every request.

    It makes every every request authenticated with default value of
    anonymous user.

    .. note::
        This middleware will always add the default user to the request
        context if no other previous authentication middleware resolved.
        So if this middleware is used it makes no sense to:
        * Use the :any:`is_authenticated` decorator.
        * Define any other authentication middleware after this one.

    Args:
        user: default anonymous user object.
    """

    challenge = None
    storage_required = True

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
