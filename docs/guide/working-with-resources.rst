Working with resources
======================

This section of documentation covers various topics related with general
API design handling specific request workflows like:

* Dealing with falcon context object.
* Using hooks and middleware classes.


.. _guide-context-aware-resources:

Dealing with falcon context objects
-----------------------------------


Falcon's ``Request`` object allows you to store some additional context data
under ``Request.context`` attribute in the form of Python dictionary. This
dictionary is available in basic falcon HTTP method handlers like:

* ``on_get(req, resp, **kwargs)``
* ``on_post(req, resp, **kwargs)``
* ``on_put(req, resp, **kwargs)``
* ``on_patch(req, resp, **kwargs)``
* ``on_options(req, resp, **kwargs)``
* ...

Graceful has slighly different design principles. If you use the generic
resource classes (i.e. :any:`RetrieveAPI`, :any:`RetrieveUpdateAPI`,
:any:`ListAPI` and so on) or the :any:`BaseResource` class with
:any:`graceful.resources.mixins` you will usually end up using only the
simple resource modification handlers:

* ``list(params, meta, **kwargs)``
* ``retrieve(params, meta, **kwargs)``
* ``create(params, meta, validated, **kwargs)``
* ...

These handlers do not have the direct access to the request and response
objects (the ``req`` and ``resp`` arguments). In most cases this is not a
proble,. Access to the request object is required usually in order to
retrieve client representation of the resource, GET parameters, and headers.
These things should be completely covered with the proper usage of
:ref:`parameter classes <guide-parameters>` and
:ref:`serializer classes <guide-serializers>`. Direct access to the
response object is also rarely required. This is because the serializers are
able to encode resource representation to the response body with negotiated
content-type. If you require additional response access (e.g. to add some
custom response headers), the best way to do that is usually through falcon
middleware classes or hooks.

Anyway, in many cases you may want to work with some unique per-request
context. Typical use cases for that are:

* Providing authentication/authorization objects using middleware classes.
* Providing session/client objects that abstract database connection and
  allow handling transactions with automated commits/rollbacks on finished
  requests.

Starting from graceful ``0.3.0`` you can define your resource class as a
`context-aware` using ``with_context=True`` keyword argument. This will change
the set of arguments provided to resource manipulation handlers in the generic
API classes:

.. code-block:: python

    from graceful.resources.generic import ListAPI
    from graceful.serializers import BaseSerializer

    class MyListResource(ListAPI, with_context=True)
        serializer = BaseSerializer()

        def list(self, params, meta, context, **kwargs)
            return {}


And in every non-generic resource class that uses mixins:

.. code-block:: python

    from graceful.resources.base import BaseResource
    from graceful.resources.mixins import ListMixin

    class MyListResource(ListMixin, BaseResource, with_context=True):

        def list(self, params, meta, context, **kwargs):
            pass


The ``context`` argument is exactly the same object as ``Request.context``
that you have access to in your falcon hooks or middleware classes.

.. note::
    **Future and backwards compatibility of context-aware resource classes**

    Every resource class in graceful ``0.x`` is not context-aware by default.
    Starting from ``0.3.0`` the `context-awareness` of the resource
    should be explicitly enabled/disabled using the ``with_context`` keyword
    argument in class definition. Not doing so will result in ``FutureWarning``
    generated on resource class instantiation.

    Starting from ``1.0.0`` all resource classes will be `context-aware` by
    default and the ``with_context`` keyword argument will become deprecated.
    The future of `non-context-aware resources` is still undecided but it is
    very likely that they will be removed completely in ``1.x`` branch.
