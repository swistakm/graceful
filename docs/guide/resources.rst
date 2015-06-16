Resources
---------

Resources are main building blocks in falcon. This is also true with
``graceful``.


The most basic resource of all is a
:class:`graceful.resources.base.BaseAPIResource` and all other resource classes
inherit from it. It will not provide you full ``graceful`` features like
object serialization, pagination etc. but it is a good starting point if you
want to build everything by yourself but still need to have some consistent
response structure and self-descriptive parameters.

In most simple case (only GET-allowed resources) the single method needs to be
implemented:


.. code-block:: python

   from graceful.resources.base import BaseAPIResource

   class SomeResource(BaseAPIResource):
        def get_meta_and_content(self, req, params, **kwargs):

            # call to super will among others populate meta with deserialized
            # dict of parameters
            meta, content = super(SomeResource, self).get_meta_and_content(
                self, req, params, **kwargs
            )

            # do with meta and content whatever you like
            # ...

            return meta, content

.. note::

   Due to how falcon works there is **always** only single instance of a
   resource class for a single registered route. Please remember to not keep
   any state inside of this object (i.e. in ``self``) between any steps of
   response generation.


Generic resources
-----------------

``graceful``provides you small set of generic resources in order to help you
describe how structured is data in your API. All of them expect that some
serializer is provided as a class level attribute. For purpose of following
examples let's assume that there is some kind of ``RawSerialiser`` that does
not know anything about structure and always return data 'as-is' in both
directions: from and to representation:

.. code-block:: python

    from graceful.serializers import BaseSerializer

    class RawSerializer():
        def to_representation(self, obj):
            return obj

        def from_representation(self, representation):
            return obj


ObjectAPIResource
~~~~~~~~~~~~~~~~~

:class:`ObjectAPIResource` represents single element resource. In ``content``
field of ``GET`` response it will return single object. On ``OPTIONS``request
it will return additional field named ``fields`` that describe all serializer
fields.

It provides ``.get_object(self, params, meta, **kwargs):`` method handler that
retrieves data about single object where:

* ``params`` - is a dictionary of retrieved parameters (after deserialization
  with parameter classes)
* ``meta`` - is a prepopulated meta dictionary for storing meta information
  about query (like processed params, processing time, etc) and does not
  represent resource data
* ``kwargs`` - is an additional dictionary of arguments retrieved from route
  template


Example usage:

.. code-block:: python

    db = SomeDBInterface()
    api = application = falcon.API()

    class FooResource(ObjectAPIResource):
        serializer = RawSerializer()

        def get_object(self, params, meta, foo_id, **kwargs):
            return db.Foo.get(id=foo_id)

    # note url template param that will be passed to `FooResource.get_object()`
    api.add_route('foo/{foo_id}', FooResource())



ListAPIResource
~~~~~~~~~~~~~~~

:class:`ListAPIResource` represents list of resource instances. In ``content``
field of ``GET`` response it will return single object. On ``OPTIONS``request
it will return additional field named ``fields`` that describe all serializer
fields.

It provides ``.get_list(self, params, meta, **kwargs):`` method handler that
retrieves data about single object where:

* ``params`` - is a dictionary of retrieved parameters (after deserialization
  with parameter classes). Those should be used for filtering of objects.
* ``meta`` - is a prepopulated meta dictionary for storing meta information
  about query (like processed params, processing time, etc) and does not
  represent resource data
* ``kwargs`` - is an additional dictionary of arguments retrieved from route
  template


Example usage:

.. code-block:: python

    db = SomeDBInterface()
    api = application = falcon.API()

    class FooListResource(ListAPIResource):
        serializer = RawSerializer()

        def get_list(self, params, meta, **kwargs):
            return db.Foo.all(id=foo_id)

    # note that in most cases there is no need do define
    # variables in url template for list type of resources
    api.add_route('foo/', FooListResource())


PaginatedListResource
~~~~~~~~~~~~~~~~~~~~~

:class:`PaginatedListResource` represents list of resource instances in the
same way as ``ListAPIResource`` (same handlers) but adds two new parameters:

* ``page_size`` - size of a single response page
* ``page`` - page count

It also includes some additional pagination information in response meta
section:

* ``page_size``
* ``page``
* ``next`` - url query string for next page (only if meta['is_more'] exist)
* ``prev`` - url query string for previous page (None if first page)

If you don't like this little opinionated meta, you can override it with
``.add_pagination_meta(params, meta)`` method handler.


``PaginatedListResource``  does not assume anything about your resources so
actual pagination must still be implemented. Anyway this class allows you to
manage params and meta for pagination in consistent way across all of your
resources:

.. code-block:: python

    db = SomeDBInterface()
    api = application = falcon.API()

    class FooPaginatedResource(PaginatedListAPIResource):
        serializer = RawSerializer()

        def get_list(self, params, meta, **kwargs):
            query = db.Foo.all(id=foo_id).offset(
                params['page'] * params['page_size']
            ).limit(
                params['page_size']
            )

            # use meta['has_more'] to find out if there are any pages behind
            # this one
            if db.Foo.count() > (params['page'] + 1) * params['page_size']:
                meta['has_more'] = True

            return query

    api.add_route('foo/', FooPaginatedtResource())
