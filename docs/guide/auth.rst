Authentication and authorization
--------------------------------

Graceful offers very simple and extendable authentication and authorization
mechanism. The main design principles for authentication and authorization
in graceful are:

* **Authentication** (identifying users) and **authorization**
  (restricting access to the endpoint) are separate processes and
  because of that they should be declared separately.
* Available authentication schemes are gloabl and always the same for whole
  application.
* Different resources usually require different permissions so authorization
  is always defined on per-resource or per-method level.
* Authentication and authorization layers communicate only through request
  context (the ``req.context`` attribute).

Thanks to these principles we are able to keep auth implementation very simple
and also allow both mechanisms to be completely optional:

* You can replace the built-in authorization tools with your own custom
  middleware classes and hooks. You can also implement authorization layer
  inside of the resource modification methods (list/create/retrieve/etc.).
* If your use case is very simple and successful authentication
  (user identification) allows for implicit access grant you can use only
  the :any:`authentication_required` decorator.
* If you want to move whole authentication layer outside of your application
  code (e.g. using specialized reverse proxy) you can easily do that.
  The only thing you need to do is to create some middleware that will properly
  modify your request context dictionary to include proper user object.


Authentication - identifying the users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to define authentication for your application you need to instantiate
one or more of the built in authentication middleware classes and configure
falcon application to use them. For example:

.. code-block:: python

    api = application = falcon.API(middleware=[
        authentication.XForwardedFor(),
        authentication.Anonymous(),
    ])


If request made the by the user meets all the requirements that are specific to
any authentication flow, the generated/retrieved user object will be included
in request context under ``req.context['user']`` key. If this context variable
exists it is a clear sign that request was succesfully authenticated.

If you use multiple different middleware classes only the first middleware
that succeeded to identify the user will be resolved. This allows for having
fallback authentication mechanism like anonymous users or users identified
by remote address.


User objects and working with user storages
```````````````````````````````````````````

Most of authentication middleware classes provided in graceful require
``user_storage`` initializations argument. This is the object
that abstracts access to the authentication database. It should implement
at least the ``get_user()`` method:

.. code-block:: python

    from graceful.authentication import BaseUserStorage

    class CustomUserStorage(BaseUserStorage):
        def get_user(
            self, identified_with, identifier,
            req, resp, resource, uri_kwargs
        ):
            ...


Accepted ``get_user()`` method arguments are:

* **identified_with** *(object)*: instance of the authentication middleware
  that provided the ``identifier`` value. It allows to distinguish different
  types of user credentials.
* **identifier** *(object)*: object that identifies the user. It is specific
  for every authentication middleware implementation. For some middlewares
  it can be a raw string value (e.g. token or API key).
* **req** *(falcon.Request)*: the request object.
* **resp** *(falcon.Response)*: the response object.
  resource (object): the resource object.
* **uri_kwargs** *(dict)*: keyword arguments from the URI template.

If user entry exists in the storage (user can be identified) the method should
return user object. This object usually is just a simple Python dictionary.
This object will be later included in the request context as
``req.context['user']`` variable. If user cannot be found in the storage
it means that his identifier is either fake or invalid. In such case this
method should always return ``None``.

.. note::

    Note that at this stage you should not verify any user permissions. If you
    can identify user but it is unpriviledged client you should still return
    the user object. Actual permission checking is a responsibility of the
    authorization layer. You should inlcude all user metadata that will be
    later required in the authorization process.

Graceful inlcudes a few useful concrete user storage implementations:

* :any:`KeyValueUserStorage`: simple implementation of user storage using any
  key-value database client as a storage backend.
* :any:`DummyUserStorage`: a dummy user storage that will always return
  the configured default user. It is useful only for testing purposes.
* :any:`IPRangeWhitelistStorage`: user storage with IP range whitelist intended
  to be used exclusively with the :any:`XForwardedFor` authentication
  middleware.


Implictit authentication without user storages
``````````````````````````````````````````````

Some built-in authentication implementations for graceful do not require
any user storage to be defined in order to work. These authentication
schemes are provided in form of following middlewares:

* :any:`authentication.XForwardedFor`: the ``user_storage`` argument is
  completely optional.
* :any:`authentication.Anonymous`: does not support ``user_storage`` argument
  at all.

If :any:`XForwardedFor` is used without any storage it will sucessfully
identify **every** request. The resulting request object will be syntetic user
dictionary in following form::

    {
        'identified_with': <authenticator>,
        'identifier': <user-address>
    }

Where ``<authenticator>`` is the authentication middleware instance (here
defaults to ``XForwardedFor``) and the ``indentity`` will be
client's address. Client address is either value of ``X-Forwarded-For`` header
or remote address taken directly from WSGI enviroment dictionary (only if
middleware is configured with ``remote_address_fallback=True``).

In case of :any:`Anonymous` the resulting user context variable will be always
the same as the value of middleware's ``user`` initialization argument.

Both :any:`XForwardedFor` (without user storage) and :any:`Anonymous` are
intended to be used only as authentication fallbacks for applications that
expect ``req.context['user']`` variable to be always available. This can be
useful for applications that identify every user to track and throttle API
usage on endpoints that do not require any authorization.


Custom authentication middleware
````````````````````````````````

The easiest way to implement custom authentication middleware is by subclassing
the :any:`BaseAuthenticationMiddleware`. The only method you need to implement
is ``identify()``. It has access to following arguments:
identify(self, req, resp, resource, uri_kwargs):

* **req** *(falcon.Request)*: falcon request object. You can read headers and
  get arguments from it.
* **resp** *(falcon.Response)*: falcon response object. Usually not accessed
  during authentication.
* **resource** *(object)*: resource object that request is routed to. May be
  useful if you want to provide dynamic realms.
* **uri_kwags** *(dict)*: dictionary of keyword arguments from URI template.

Aditionally you can control further the behaviour of authentication middleware
using following class attributes:

* ``only_with_storage``: if it is set to True, it will be impossible to
  initialize the middleware without ``user_storage`` argument.
* ``challenge``: returns the challenge string that will be inlcuded in
  ``WWW-Authenticate`` header on unauthorized request responses. This has
  effect only in resources protected with :any:`authentication_required`.


Authorization - restricting access to the endpoint
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The recommended way to implement authorization in graceful is through falcon
hooks that can be applied to whole resources and HTTP method handlers:

.. code-block:: python

    import falcon

    from graceful.resources.generic import ListAPI

    falcon.before(my_authorization_hook)
    class MyListResource(ListAPI):
        ...

        @falcon.before(my_other_authorization_hook)
        def on_post(self, *args, **kwargs)
            return super().on_post()


Authorization hooks depend solely on user context stored under
``req.context['user']``. The usual authorization hook implementation does two
things:

* Check if the ``'user'`` variable is available in ``req.context`` dictionary.
  If it isn't then raise the ``falcon.HTTPForbidden`` exception.
* Verify user object content (e.g. check his group) and raise the
  ``falcon.HTTPForbidden`` exception if does not meet specific requirements.

Example of customizable authorization hook implementation that requires
specific user group to be assigned could be as follows:

.. code-block:: python

    import falcon

    def group_required(user_group):

        @falcon.before
        def authorization_hook(req, resp, resource, uri_kwargs)
            try:
                user = req.context['user']

            except KeyError:
                raise falcon.HTTPForbidden(
                    "Forbidden",
                    "Could not identify the user!"
                )

            if user_group not in user.get('groups', set()):
                raise falcon.HTTPForbidden(
                    "Forbidden",
                    "'{}' group required!".format(user_group)
                )

Depending on your application design and complexity you will need different
authorization handling. The way how you grant/deny access also depends highly
on the structure of your user objects and the preferred user storage.
This is why graceful provides only one basic authorization utility - the
:any:`authentication_required` decorator.

The :any:`authentication_required` decorator ensures that request successfully
passed authentication. If none of the authentication middlewares succeeded
to identify the user it will raise ``falcon.HTTPUnauthorized``
exception and include list of available authentication challenges in the
``WWW-Authenticate`` response header. If you use this decorator you don't need
to check for ``req.context['user']`` existence in your custom authorization
hooks (still, it is a good practice to do so).

Example usage is:

.. code-block:: python

    from graceful import authorization
    from graceful.resources.generic import ListAPI

    from myapp.auth import group_required

    @authentication_required
    @group_required("admin")
    class MyListResource(ListAPI):
        ...

        @falcon.before(my_other_authorization_hook)
        def on_post(self, *args, **kwargs)
            return super().on_post()

Heterogenous authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Graceful does not allow you to specify unique per-resource or per-method
authentication schemes. This allows for easier implementation but may not
cover every use case possible.

If you need to restrict some authentication methods to specific resources
(e.g. some custom auth only for internal use) the best way is to handle this
through separate application deployments.


.. _auth-practical-example:

Practical example -- authentication with redis backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's assume we want to build simple REST API application supporting two
authentication schemes:

* :any:`Token` access authentication with ``Authorization: Token`` HTTP header
* :any:`Basic` access authentication with ``Authorization: Basic`` HTTP header
  as specified by `RFC 7617`_.

As a user database we will use :any:`KeyValueUserStorage` storage class which is
compatible with any key-value database client that provides two simple methods:

* ``set(key, value)``: set key value in the storage. Both key and value should
  be strings.
* ``get(key)``: get key value from the storage. Both key and return value
  should be string.


First step is to create a key-value store client user storage intance that
will be used by both authentication middlewares. With redis and
:any:`KeyValueUserStorage` this is very simple:

.. code-block:: python

    from redis import StrictRedis as Redis
    from graceful.authentication import KeyValueUserStorage

    auth_storage = KeyValueUserStorage(Redis())

This storage can be used by many different authentication middlewares at the
same time. It will properly prefix every Redis key with middleware name to make
sure different types of user entries do not collide with each other.

The only problem is that default implementation of
``KeyValueUserStorage.hash_identifier(identified_with, identifier)`` method expects
that ``identifier`` argument is a single string argument. The :any:`Basic`
authentication middleware generates identifiers in form of
``(username, password)`` two-tuples. Fortunately you don't need to use
subclassing in order to override this method behavior. The
:any:`hash_identifier` method is a `single-dispatch generic function`_ so you
can easily create custom handlers for specific authentication middleware types.

We definitely don't want to store user passwords in plain text. Let's register
simple ``hash_identifier`` handler for :any:`Basic` access authentication that
will properly prepare password hash using SHA1 algorithm:

.. code-block:: python

    from hashlib import sha1

    from graceful.authentication import Basic


    @auth_storage.hash_identifier.register(Basic)
    def _(identified_with, identifier):
        return ":".join((
            identifier[0],
            hashlib.sha1(identifier[1].encode()).hexdigest()
        ))

Default ``hash_identifier`` leaves single-string identifiers untouched so it
may be a good idea to hash token identifiers in similar fashion too:

.. code-block:: python

    @auth_storage.hash_identifier.register(Token)
    def _(identified_with, identifier):
        return hashlib.sha1(identifier[1].encode()).hexdigest()

.. note::
    Really secure `password verification`_ mechanism would require proper
    time-consuming hashing algorithm that would prevent application from
    brute-force and timing attacks. Anyway, for real end-user applications you
    would probably use a session cookie for authentication rather than basic
    access authentication. For such case simple SHA1 hashing may not be the
    best solution. Still, **basic access authentication** is a simple
    alternative to custom authentication headers and/or GET parameters when
    communicating in **server-to-server fashion** over the **secure channel**.

Our authentication setup is almost finished. The last things to do is to
initialize authentication middlewares and setup a very basic authorization
to API resources. Following is the code for a very small application that
protects its resources with :any:`Token` and :any:`Basic` authentication
middlewares:

.. code-block:: python

    import hashlib

    from redis import StrictRedis as Redis
    import falcon

    from graceful.resources.generic import Resource
    from graceful.authentication import KeyValueUserStorage, Token, Basic
    from graceful.authorization import authentication_required

    @authentication_required
    class Me(Resource, with_context=True):
        def retrieve(self, params, meta, context):
            return context.get('user')


    auth_storage = KeyValueUserStorage(Redis())


    @auth_storage.hash_identifier.register(Basic)
    def _(identified_with, identifier):
        return ":".join((
            identifier[0],
            hashlib.sha1(identifier[1].encode()).hexdigest()
        ))


    @auth_storage.hash_identifier.register(Token)
    def _(identified_with, identifier):
        return hashlib.sha1(identifier[1].encode()).hexdigest()

    api = application = falcon.API(
        middleware=[
            Token(auth_storage),
            Basic(auth_storage),
        ]
     )

    api.add_route('/me/', Me())

Now you can easily create new user entries using Pyhton console::

    >>> from auth_app import auth_storage, Token, Basic
    >>> auth_storage.register(Token(auth_storage), 'mytoken', {"user": "me with token"})
    >>> auth_storage.register(Basic(auth_storage), ['myusername', 'mysecretpassword'], {"user": "me with password"})

... check if they are successfully saved in Redis::

    $ redis-cli keys '*'
    1) "users:Token:95cb0bfd2977c761298d9624e4b4d4c72a39974a"
    2) "users:Basic:myusername:08cd923367890009657eab812753379bdb321eeb"


... and verify authentication using HTTP client (here with ``httpie``)::

    $ http localhost:8000/me
    HTTP/1.1 401 Unauthorized
    Connection: close
    Date: Thu, 23 Mar 2017 16:09:55 GMT
    Server: gunicorn/19.6.0
    content-length: 91
    content-type: application/json
    vary: Accept
    www-authenticate: Token, Basic realm=api

    {
        "description": "This resource requires authentication",
        "title": "Unauthorized"
    }

    $ http localhost:8000/me --auth myusername:mysecretpassword
    HTTP/1.1 200 OK
    Connection: close
    Date: Thu, 23 Mar 2017 16:08:53 GMT
    Server: gunicorn/19.6.0
    content-length: 76
    content-type: application/json

    {
        "content": {
            "user": "me with password"
        },
        "meta": {
            "params": {
                "indent": 0
            }
        }
    }

    $ http localhost:8000/me 'Authorization:Token mytoken'
    HTTP/1.1 200 OK
    Connection: close
    Date: Thu, 23 Mar 2017 16:09:39 GMT
    Server: gunicorn/19.6.0
    content-length: 73
    content-type: application/json

    {
        "content": {
            "user": "me with token"
        },
        "meta": {
            "params": {
                "indent": 0
            }
        }
    }

.. _RFC 7617: https://tools.ietf.org/html/rfc7616
.. _single-dispatch generic function: https://docs.python.org/3/library/functools.html#functools.singledispatch
.. _password verification: https://en.wikipedia.org/wiki/Cryptographic_hash_function#Password_verification

