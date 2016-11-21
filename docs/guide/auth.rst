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
        authentication.Anonymous({"user": "anonymous"})
    ])


If request made the by the user meets all the requirements that are specific to
any authentication flow, the generated/retrieved user object will be included
in request context under ``req.context['user']`` key. If this context variable
exists it is a clear sign that request was succesfully authenticated.

If you use multiple different middleware classes only the first middleware
that succedded to identify the user will be resolved. This allows for having
fallback authentication mechanism like anonymous users or users identified
by remote address.


User objects and working with user storages
```````````````````````````````````````````

Most of authentication middleware classes provided in graceful require
``user_storage`` as one of initializations argument. This is the object
that abstracts access to the authentication database and should implement
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

* **identified_with** *(str)*: instance of the authentication middleware that
  provided the ``identifier`` value. It allows to distinguish different types
  of user credentials.
* **identifier** *(str)*: string that identifies the user (it is specific
  for every authentication middleware implementation).
* **req** *(falcon.Request)*: the request object.
* **resp** *(falcon.Response)*: the response object.
  resource (object): the resource object.
* **uri_kwargs** *(dict)*: keyword arguments from the URI template.

If user exists in the storage (user can be identified) the method should
return user object. This object is usually just a simple Python dictionary.
This object will be later included in the request context as
``req.context['user']`` variable. If user cannot be found in the storage
it means that his identifier is either fake or invalid. In such case this
method should always return ``None``.

.. note::

    Note that at this stage you should not verify any user permissions. If you
    can identify user but it is unpriviledged client you should still return
    the user object. Actual permission checking belongs to authorization layer.
    You should definitely inlcude all user metadata data that will be later
    required in the authorization process.

Graceful inlcudes a few useful concrete user storage implementations:

* :any:`RedisUserStorage`: simple implementetion of user storage using Redis
  as a storage backend.
* :any:`DummyUserStorage`: a dummy user storage that will always return
  the configured default user. It is useful only for testing purposed.
* :any:`IPWhitelistStorage`: an user storage with IP whitelist intended to be
  used exclusively with the :any:`XForwardedFor` authentication middleware.


Implictit authentication without user storages
``````````````````````````````````````````````

Some built-in authentication implementations for graceful do not require
any user storage to be defined in order to work. These authentication methods
are:

* :any:`authentication.XForwardedFor`: the ``user_storage`` argument is
  completely optional.
* :any:`authentication.Anonymous`: does not support ``user_storage`` argument
  at all.

If :any:`XForwardedFor` is used without any storage it will sucessfully
identify **every** request. The resulting request object will be syntetic user
dictionary in following form::

    {
        'identified_with': <authenticator-name>,
        'identifier': <user-address>
    }

Where ``<authenticator-name>`` will be the configured name of authentication
middleware (here defaults to ``XForwardedFor``) and the ``indentity`` will be
client's address (either value of ``X-Forwarded-For`` header or remote address
directly from WSGI enviroment dictionary).

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
(e.g. some custom auth only for internal use) the best way to handle that
is through separate application deployments.
