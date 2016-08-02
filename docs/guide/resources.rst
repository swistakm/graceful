Resources
---------

Resources are main building blocks in falcon. This is also true with
``graceful``.


The most basic resource of all is a :class:`graceful.resources.base.BaseResource`
and all other resource classes in in this package inherit from ``BaseResource``.
It will not provide you with full set graceful features (like
object serialization, pagination, resource fields descriptions etc.)
but it is a good starting point if you want to build everything by yourself
but still need to have some consistent response structure and
self-descriptive parameters.

In most cases (simple GET-allowed resources) you need only to provide
your own http GET method handler like following:


.. code-block:: python

   from graceful.resources.base import BaseResource
   from graceful.parameters import StringParam, IntParam

   class SomeResource(BaseResource):
        # describe how HTTP query string parameters are handled
        some_param = StringParam("example string query string param")
        some_other_param = IntParam("example integer query string param")


        def on_get(self, req, resp):
            # retrieve dictionary of query string parameters parsed
            # and validated according to resource class description
            params = self.require_params(req)

            ## create your own response like always:
            # resp.body = "some content"

            ## or use following:
            # self.make_body(resp, params, {}, 'some content')

.. note::

   Due to how falcon works there is **always** only single instance of a
   resource class for a single registered route. Please remember to not keep
   any state inside of this object (i.e. in ``self``) between any steps of
   response generation.


