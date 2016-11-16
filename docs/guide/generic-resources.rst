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

    # note: url template kwarg that will be passed to
    #       `FooResource.get_object()`
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

    class FooListResource(ListAPI):
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
POST or PATCH request body.

It expects from you to implement same handlers as for :class:`ListAPI`
and also new ``.create(self, params, meta, validated, **kwargs)``
and (optionally) ``.create_bulk(self, params, meta, validated, **kwargs)``
method handlers that are able to create single single and multiple objects
(e.g. in some storage). Created object may or may not be returned in response
'content' section (this is optional)

``create()`` accepts following arguments:

* **params** *(dict):* dictionary of parsed parameters accordingly
  to definitions provided as resource class atributes.
* **meta** *(dict):* dictionary of meta parameters anything added
  to this dict will will be later included in response
  'meta' section. This can already prepopulated by method
  that calls this handler.
* **validated** *(dict):* a **single dictionary** of internal object fields
  values after converting from representation with full validation performed
  accordingly to definition contained within serializer instance.
* **kwargs** *(dict):* dictionary of values retrieved from route url
  template by falcon. This is suggested way for providing
  resource identifiers.

``create_bulk()`` accepts following arguments:

* **params** *(dict):* dictionary of parsed parameters accordingly
  to definitions provided as resource class atributes.
* **meta** *(dict):* dictionary of meta parameters anything added
  to this dict will will be later included in response
  'meta' section. This can already prepopulated by method
  that calls this handler.
* **validated** *(dict):* a **list of multiple dictionaries** of internal
  objects' field values after converting from representation with
  full validation performed accordingly to definition contained within
  serializer instance.
* **kwargs** *(dict):* dictionary of values retrieved from route url
  template by falcon. This is suggested way for providing
  resource identifiers.


If ``create()`` and ``create_bulk()`` return any value then it should have
same form compatible with the return value of ``retrieve()`` because it will
be again translated into representation with serializer. Of course ``create()``
should return single instance of resource but ``create_bulk()`` should return
collection of resources.

Note that default implementation of :any:`ListCreateAPI.create_bulk()` is very
simple and may not be suited for every use case. If you want to use it please
refer to :ref:`bulk-creation-guide`.

Example usage:

.. code-block:: python

    db = SomeDBInterface()
    api = application = falcon.API()

    class FooListResource(ListCreateAPI):
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
of :class:`ListAPI` and :class:`ListAPI` classes that support simple pagination
with following parameters:

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

    If you don't like anything about this opinionated meta section that
    paginated generic resources provide, you can always override it with
    own ``add_pagination_meta(params, meta)`` method handler.


Generic resources without serialization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you don't like how serializers work there are also two very basic generic
resources that does not rely on serializers: :class:`Resource` and
:class:`ListResource`. They can be extended with mixins found in
:any:`graceful.resources.mixins` module and provide the same method handlers
like the generic resources that utilize serializers (i.e. ``list()``,
``retrieve()``, ``update()`` and so on). Note that they do not perform anything
beyond content-type level serialization.


.. _bulk-creation-guide:

Guide for creating resources in bulk
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


:class:`ListCreateAPI` ships with default implementation of ``create_bulk()``
method that will call the ``create()`` method separately for every resource
instance retrieved from request payload. The actual code is following:

.. code-block:: python

   def create_bulk(self, params, meta, **kwargs):
        validated = kwargs.pop('validated')
        return [self.create(params, meta, validated=item) for item in validated]

This approach to bulk resource creation may not be the most performant one if
you save resource instance to your storage on every ``create()`` call.
The other concern is whether you care about data consistency in your storage
and want to ensure the "all or nothing" semantics. With default bulk creation
handler it may be hard to enforce such contraints. Anyway, you can easily
override this method to suit your own needs.

There are at least three ways you can handle bulk resource creation in graceful:

* *Completely separate bulk and single resource creation*: allow ``create()``
  and ``create_bulk()`` handlers to have their own separate code responsible
  for saving data in the storage.
* *Deffered saves*: Allow your ``create()`` handler to skip saves if specific
  keyword parameter is set and then do your saves in th ``create_bulk()``
  handler.
* *Utilize your storage transactions*: Wrap your data processing with
  per-request transaction to ensure "all or nothing" semantics on database
  level.


Completely separate bulk and single resource creation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This approach is simplest to implement but makes only sense if the process
of your resource creation is very simple and heavily relies on serializers
to validate and prepare your data before save.

Assume your API allows to create and retrieve simple documents in some simple
storage that may even not be a real database. Good example would be an API
dealing with Solr search engine:

.. code-block:: python

    from pysolr import Solr

    from graceful.serializers import BaseSerializer
    from graceful.fields import StringField
    from graceful.resources.generic import ListCreateAPI

    solr = Solr("<solr url>", "<solr port>")


    class DocumentSerializer(BaseSerializer):
        text = StringField("Document content")
        author = StringField(
            "Document author",
            # note: Assume that due to legacy reasons this field
            #       is stored under different name in Solr.
            #       graceful is great in dealing with such problems!
            source="autor_name_t"
        )


    class DocumentsAPI(ListCreateAPI):
        def list(self, params, meta, **kwargs):
            return solr.search("*:*")

        def create(self, params, meta, validated, **kwargs):
            solr.add([validated])
            # note: return document back so its representation
            #       can be included in response body
            return validated


Solr search engine is especially good example here because it will not handle
well multiple single-ducument save requests and the best approach is to
batch them. The ``pysolr`` module (popular library for integration with solr)
allows you to save multiple documents with single ``Solr.add()`` call.
Actually, it even encourages you to batch documents using single call because
it accepts only list as input argument.

Let's override the default ``create_bulk()`` so it will save all the documents
it receives as the ``validated`` argument without calling ``create()`` handler:

.. code-block:: python

    class DocumentsAPI(ListCreateAPI):
        def list(self, params, meta, **kwargs):
            return solr.search("*:*")

        def create(self, params, meta, validated, **kwargs):
            solr.add([validated])
            # note: return document back so its representation
            #       can be included in the response body
            return validated

        def create_bulk(self, params, meta, validated, **kwargs):
            solr.add(validated)
            # note: return documents back so their representation
            #       can be included in the response body
            return validated


Note that above technique works best for simple use cases where the
``validated`` argument represents complete data that can be easily saved
directly to your storage without any further modification.

If you need any additional processing of resources in your custom ``create()``
and ``create_bulk()`` methods before saving them to your storage,
the code can quickly become hard to mantain. Anyway, you can start with this
approach and refactor it later into *deferred saves* pattern as these two are
very alike and offer similar advantages.


Deferred saves
^^^^^^^^^^^^^^

In previous section we said that having separate code that independently saves
*single resource* and *resources in bulk* may not be a best approach if you
need to make some additional data processing before saves. No matter
if you do a non-serializer-based data validation or talk to some other external
services, you will need to duplicate this additional processing code in both
handlers. With proper approach you can limit the code duplication by extrating
your resource processing procedures to additial methods but it will eventually
make things unnecessarily complex and will still be hard to maintain.

A little improvement to previous code is to reuse single resource creation
handler in your custom ``create_bulk()`` implementation but allow the
``create()`` handler to skip saving data to storage on the caller's demand.
Thus any per-resource processing will always stay in the ``create()`` handler
code and the ``create_bulk()`` will be responsible only for saving the data in
bulk:

.. code-block:: python

    class DocumentsAPI(ListCreateAPI):
        def list(self, params, meta, **kwargs):
            return solr.search("*:*")

        def create(self, params, meta, validated, skip_save=False, **kwargs):
            # do some additional processing like adding defaults etc.
            validated['created_at'] = time.time()

            # note: skip_save defaults to False on ordinary POST requests
            #       this means ``create()`` was called in single-resource mode
            if not skip_save:
                solr.add([validated])

            # note: return document back so its representation
            #       can be included in the response body
            return validated

        def create_bulk(self, params, meta, validated, **kwargs):
            validated = kwargs.pop('validated')

            processed = [
                self.create(params, meta, item, skip_save=True)
                for item in validated
            ]
            solr.add(processed)

            return processed


This way you can be sure that anything you add to the  ``create()`` handler
will also affect the resources created in bulk. Additionally your API is more
efficient because it can save the data in bulk with single request to your
storage backend instead of making multiple requests.


Utilize your storage transactions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes you may not concerned about the performance of multiple small saves
but only want to have the "all or nothing" semantics of the bulk creation
method. If the integration with your storage backend allows you to enforce
transactions on the block of code you can easily use such feature to make sure
that all the separate saves done with ``create()`` handler will take effect
in the "all or nothing" manner. Good use case for such appoach could be working
with any RDBMS that allows to use transactions.

Let's assume you have a per-request ``session`` object that wraps the
integration with the storage backend and allows you to set savepoints and
commit/rollback transactions. Many ORM layers (e.g. SQLAlchemy) offer such
kind of object code for such technique may look very simillar for different
storage providers:

.. code-block:: python

    # note: example sqlachemy integration could work that way
    engine = create_engine("...")
    Session = sessionmaker(bind=engine)

    class MyAPI(ListCreateAPI):
        def on_post(req, resp, **kwargs):
            # inject session object into kwargs so it can be later
            # used by ``create()`` handler to manipulate storage
            # and manage transaction
            session = Session()
            try:
                super().on_post(req, resp, session=session, **kwargs)
            except:
                session.rollback()
                raise
            else:
                session.commit()

        def on_patch(req, resp, **kwargs):
            # inject session object into kwargs so it can be later
            # used by ``create_bulk()`` handler to manipulate storage
            # and manage transaction
            session = Session()
            try:
                super().on_patch(req, resp, session=session, **kwargs)
            except:
                session.rollback()
                raise
            else:
                session.commit()
