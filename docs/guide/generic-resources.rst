Generic API resources
---------------------

graceful provides you with some set of generic resources in order to help you
describe how structured is data in your API. All of them expect that some
serializer instance is provided as a class level attribute. Serializer will
handle describing resource fields and also translation between
resource representation and internal object values that you use inside of
your application.


RetrieveAPI
~~~~~~~~~~~

:class:`RetrieveAPI` represents single element serialized resource. In 'content'
section of GET response it will return single object. On OPTIONSrequest
it will return additional field named 'fields' that describes all serializer
fields.

It expects from you to implement ``.retrieve(self, params, meta, **kwargs)``
method handler that retrieves single object (e.g. from some storage) that will
be later serialized using provided serializer.

``retrieve()`` accepts following arguments:

* **params** *(dict):* dictionary of parsed parameters accordingly
  to definitions provided as resource class atributes.
* **meta** *(dict):* dictionary of meta parameters anything added
  to this dict will will be later included in response
  'meta' section. This can already prepopulated by method
  that calls this handler.
* **kwargs** *(dict):* dictionary of values retrieved from route url
  template by falcon. This is suggested way for providing
  resource identifiers.


Example usage:

.. code-block:: python

    db = SomeDBInterface()
    api = application = falcon.API()

    class FooResource(RetrieveAPI):
        serializer = RawSerializer()

        def retrieve(self, params, meta, foo_id, **kwargs):
            return db.Foo.get(id=foo_id)

    # note url template param that will be passed to `FooResource.get_object()`
    api.add_route('foo/{foo_id}', FooResource())



RetrieveUpdateAPI
~~~~~~~~~~~~~~~~~

:class:`RetrieveUpdateAPI` extends :class:`RetrieveAPI` with capability to
update objects with new data from resource representation provided in
PUT request body.

It expects from you to implement same handlers as for :class:`RetrieveAPI`
and also new ``.update(self, params, meta, validated, **kwargs)`` method handler
that updates single object (e.g. in some storage). Updated object may or may
not be returned in response 'content' section (this is optional)

``update()`` accepts following arguments:

* **params** *(dict):* dictionary of parsed parameters accordingly
  to definitions provided as resource class atributes.
* **meta** *(dict):* dictionary of meta parameters anything added
  to this dict will will be later included in response
  'meta' section. This can already prepopulated by method
  that calls this handler.
* **validated** *(dict):* dictionary of internal object fields values
  after converting from representation with full validation performed
  accordingly to definition contained within serializer instance.
* **kwargs** *(dict):* dictionary of values retrieved from route url
  template by falcon. This is suggested way for providing
  resource identifiers.

If update will return any value it should have same form as return value
of ``retrieve()`` because it will be again translated into representation
with serializer.


Example usage:

.. code-block:: python

    db = SomeDBInterface()
    api = application = falcon.API()

    class FooResource(RetrieveUpdateAPI):
        serializer = RawSerializer()

        def retrieve(self, params, meta, foo_id, **kwargs):
            return db.Foo.get(id=foo_id)

        def update(self, params, meta, foo_id, **kwargs):
            return db.Foo.update(id=foo_id)

    # note url template param that will be passed to `FooResource.get_object()`
    api.add_route('foo/{foo_id}', FooResource())


RetrieveUpdateDeleteAPI
~~~~~~~~~~~~~~~~~~~~~~~

:class:`RetrieveUpdateDeleteAPI` extends :class:`RetrieveUpdateAPI` with
capability to delete objects using DELETE requests.

It expects from you to implement same handlers as for :class:`RetrieveUpdateAPI`
and also new ``.delete(self, params, meta, **kwargs)`` method handler
that deletes single object (e.g. in some storage).

``delete()`` accepts following arguments:

* **params** *(dict):* dictionary of parsed parameters accordingly
  to definitions provided as resource class atributes.
* **meta** *(dict):* dictionary of meta parameters anything added
  to this dict will will be later included in response
  'meta' section. This can already prepopulated by method
  that calls this handler.
* **kwargs** *(dict):* dictionary of values retrieved from route url
  template by falcon. This is suggested way for providing
  resource identifiers.


Example usage:

.. code-block:: python

    db = SomeDBInterface()
    api = application = falcon.API()

    class FooResource(RetrieveUpdateAPI):
        serializer = RawSerializer()

        def retrieve(self, params, meta, foo_id, **kwargs):
            return db.Foo.get(id=foo_id)

        def update(self, params, meta, foo_id, **kwargs):
            return db.Foo.update(id=foo_id)

        def delete(self, params, meta, **kwargs):
            db.Foo.delete(id=foo_id)

    # note url template param that will be passed to `FooResource.get_object()`
    api.add_route('foo/{foo_id}', FooResource())


ListAPI
~~~~~~~

:class:`ListAPI` represents list of resource instances. In 'content'
section of GET response it will return list of serialized objects
representations. On OPTIONS request it will return additional
field named 'fields' that describes all serializer fields.


It expects from you to implement ``.list(self, params, meta, **kwargs)``
method handler that retrieves list (or any iterable) of objects
(e.g. from some storage) that will be later serialized using provided
serializer.

``list()`` accepts following arguments:

* **params** *(dict):* dictionary of parsed parameters accordingly
  to definitions provided as resource class atributes.
* **meta** *(dict):* dictionary of meta parameters anything added
  to this dict will will be later included in response
  'meta' section. This can already prepopulated by method
  that calls this handler.
* **kwargs** *(dict):* dictionary of values retrieved from route url
  template by falcon. This is suggested way for providing
  resource identifiers.

Example usage:

.. code-block:: python

    db = SomeDBInterface()
    api = application = falcon.API()

    class FooListResource(ListAPIResource):
        serializer = RawSerializer()

        def list(self, params, meta, **kwargs):
            return db.Foo.all(id=foo_id)

    # note that in most cases there is no need do define
    # variables in url template for list type of resources
    api.add_route('foo/', FooListResource())


ListCreateAPI
~~~~~~~~~~~~~

:class:`ListCreateAPI` extends :class:`ListAPI` with capability to
create new objects with data from resource representation provided in
POST request body.

It expects from you to implement same handlers as for :class:`ListAPI`
and also new ``.create(self, params, meta, validated, **kwargs)`` method handler
that creates single object (e.g. in some storage). Created object may or may
not be returned in response 'content' section (this is optional)

``create()`` accepts following arguments:

* **params** *(dict):* dictionary of parsed parameters accordingly
  to definitions provided as resource class atributes.
* **meta** *(dict):* dictionary of meta parameters anything added
  to this dict will will be later included in response
  'meta' section. This can already prepopulated by method
  that calls this handler.
* **validated** *(dict):* dictionary of internal object fields values
  after converting from representation with full validation performed
  accordingly to definition contained within serializer instance.
* **kwargs** *(dict):* dictionary of values retrieved from route url
  template by falcon. This is suggested way for providing
  resource identifiers.

If ``create()`` will return any value it should have same form as return value
of ``retrieve()`` because it will be again translated into representation
with serializer.

Example usage:

.. code-block:: python

    db = SomeDBInterface()
    api = application = falcon.API()

    class FooListResource(ListAPIResource):
        serializer = RawSerializer()

        def list(self, params, meta, **kwargs):
            return db.Foo.all(id=foo_id)

        def create(self, params, meta, validated, **kwargs):
            return db.Foo.create(**validated)

    # note that in most cases there is no need do define
    # variables in url template for list type of resources
    api.add_route('foo/', FooListResource())


Paginated generic resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`PaginatedListAPI` and :class:`PaginatedListCreateAPI` are versions
of respecrively :class:`ListAPI` and :class:`ListAPI` classes that supply
with simple pagination build with following parameters:

* **page_size:** size of a single response page
* **page:** page count

They also will 'meta' section with following information on GET requests:

* ``page_size``
* ``page``
* ``next`` - url query string for next page (only if ``meta['is_more']`` exists
  and is ``True``)
* ``prev`` - url query string for previous page (``None`` if first page)

Paginated variations of generic list resource do not assume anything about
your resources so actual pagination must still be implemented inside of
``list()`` handlers. Anyway this class allows you to manage params and meta
for pagination in consistent way across all of your resources if you only
decide to use it:

.. code-block:: python

    db = SomeDBInterface()
    api = application = falcon.API()

    class FooPaginatedResource(PaginatedListAPI):
        serializer = RawSerializer()

        def list(self, params, meta, **kwargs):
            query = db.Foo.all(id=foo_id).offset(
                params['page'] * params['page_size']
            ).limit(
                params['page_size']
            )

            # use meta['has_more'] to find out if there are
            # any pages behind this one
            if db.Foo.count() > (params['page'] + 1) * params['page_size']:
                meta['has_more'] = True

            return query

    api.add_route('foo/', FooPaginatedtResource())


.. note::

    If you don't like anything about little opinionated meta that paginated
    generic resources provide you can olways override it with
    ``.add_pagination_meta(params, meta)`` method handler.


Generic resources without serialization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you don't like how serializers work there are also two very basic generic
resources that does not rely on serializers: :class:`Resource` and
:class:`ListResource`. They can be extended with mixins found in
:any:`graceful.resources.mixins` module and provide same method handlers like
generic resources that utilize serializers (``list()``, ``retrieve()``,
``update()`` etc.) but do not perform anything more beyond content-type level
serialization.
