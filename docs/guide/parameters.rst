.. _guide-parameters:

Parameters
----------

Parameters provide a way to describe and evaluate all request query params
that can be used in your API resources.

New parameters are added to resources as class attributes:

.. code-block:: python

    from graceful.parameters import StringParam, IntParam
    from graceful.resources.base import BaseResource

    class SomeResource(BaseResource):
        filter_by_name = StringParam("Filter resource instances by their name")
        depth = IntParam("Set depth of search")


Class attribute names map directly to names expected in the query string. For
example the valid query strings in scope of preceding definition could be:

- ``filter_by_name=cats``
- ``filter_by_name=dogs&depth=2``

All param classes accept this set of arguments:

- **details** *(str):* verbose description of parameter. Should contain all
  information that may be important to your API user and will be used for
  describing resource on ``OPTIONS`` requests and ``.describe()``
  call.

- **label** *(str):* human readable label for this parameter (it will be used for
  describing resource on OPTIONS requests).

  *Note that it is recomended to use parameter names that are self-explanatory
  intead of relying on param labels.*

- **required** *(bool):* if set to ``True`` then all GET, POST, PUT,
  PATCH and DELETE requests will return ``400 Bad Request`` response
  if query param is not provided.

- **default** *(str):* set default value for param if it is not
  provided in request as query parameter. This MUST be a raw string
  value that will be then parsed by ``.value()`` handler.

  If default is set and ``required`` is ``True`` it will raise
  ``ValueError`` as having required parameters with default
  value has no sense.

- **param** *(str):* set to ``True`` if multiple occurences of this parameter
  can be included in query string, as a result values for this parameter will
  be always included as a list in params dict. Defaults to ``False``.

  .. note::
     If ``many==False`` and client inlcudes multiple values for this
     parameter in query string then only one of those values will be
     returned, and it is undefined which one.


For list of all available parameter classes please refer to
:any:`graceful.parameters` module reference.

If you are using the bare falcon HTTP method handlers and sublcass directly
from :class:`graceful.resources.base.BaseResource` then you can access all
deserialized query parameters as dictionary using ``require_params(req)``
method:


.. code-block:: python

    from graceful.parameters import StringParam, IntParam
    from graceful.resources.base import BaseResource

    class SomeResource(BaseResource):
        filter_by_name = StringParam("Filter resource instances by their name")
        depth = IntParam("Set depth of search")

        def on_get(self, req, resp):
            params = self.require_params(req)


The ``self.require_params(req)`` will try to retrieve all of described query
parameters, validate them and populate with defaults if they were not found
in the query string. This method will also take care of raising the
``falcon.errors.HTTPInvalidParam`` if:

* parameter specified as ``required=True`` was not provided
* parameter could not be parsed/validated (i.e. ``value()`` handler raised
  ``ValueError``)

Note that you do not need to handle this exception manually. It will be later
automatically transformed to ``400 Bad Request`` by falcon if not catched
by ``try .. except`` clause.

If you are using generic resource classes from :any:`graceful.resources.generic`
like :any:`ListAPI` or :any:`RetrieveAPI` the params retrieval step is done
automatically and you do not need to care. Parameters dict will be provided
in applicable retrieval/modification method handler (``list()``, ``update()``,
``retrieve`` etc.) and these methods will be executed only if call to
``self.require_params(req)`` succeeded without raising any exceptions.


Custom parameters
~~~~~~~~~~~~~~~~~

Although *graceful* ships with some set of predefined parameter classes it is
very likely that you need something that is not yet covered because:

* it is *not yet* covered
* is very specific to your application
* it can be implemented in many ways and it is impossible to decide which is
  best without being too opinionated.

New parameter types can be created by subclassing :any:`BaseParam` and
and implementing ``.value(raw_value)`` method handler. ``ValueError`` raised
in this handler will eventually result in ``400 Bad Request`` response.

Two additional class-level attributes help making more verbose parameter
description:

* **type** - string containig name of primitive data type like: "int", "string",
  "float" etc. For most custom parameters this will be simply "string" and it
  is used only for describtions so make sure it is something truely generic
  or well described in your API documentation
* **spec** - two-tuple containing link name, and link url to any external
  documentation that you may find helpful for developers.


Here is example of custom parameter that handles validation of alpha2 country
codes using pycountry module:

.. code-block:: python

    import pycountry

    class LanguageParam(BaseParam):
        """
        This param normalizes language code passed to is and checks if it is valid
        """

        type = 'ISO 639-2 alpha2 language code'
        spec = (
            'ISO 639-2 alpha2 code list',
            "http://www.loc.gov/standards/iso639-2/php/code_list.php",
        )

        def value(self, raw_value):
            try:
                # normalize code since we store then lowercase
                normalized = raw_value.lower()
                # first of all check if country so no query will be made if it is
                # invalid
                pycountry.languages.get(alpha2=normalized)

                return normalized

            except KeyError:
                raise ValueError(
                    "'{code}' is not valid alpha2 language code"
                    "".format(code=raw_value)
                )

Parameter validation
~~~~~~~~~~~~~~~~~~~~

Custom parameters are great for defining new data types that can be passed
through HTTP query string or handling very specific cases like country codes,
mime types, or even database filters. Still it may be sometimes an overkill
to define new parameter class to do something as simple as ensure min/max
bounds for numeric value or define as set of allowed choices.

All of basic parameters available in graceful accept ``validators`` keyword
argument that accepts a list of validation functions. These function will be
always called upon parameter retrieval. This functionality allows you to
quickly extend the semantic of your parameters without the need of subclassing.

A validator is any callable that accepts single positional argument
that will be a value returned from call to the ``value()`` handler of parameter
class. If validation funtion fails it is supposed to return
:class:`graceful.errors.ValidationError` that will be later translated to
proper HTTP error response. Following is example of simple validation function
which ensures that parameter string is palindrome:

.. code-block:: python

    from graceful.resources.base import BaseResource
    from graceful.parameters import StrParam
    from graceful.errors import ValidationError

    def is_palindrome(value):
        if value != value[::-1]:
            raise ValidationError("{} is not a palindrome")


    class FamousPhrases(Resource):
        palindrome_query = StrParam(
            "Palindrome text query", validators=[is_palindrome]
        )


Validators always work on deserialized values and this allows to easily reuse
the same code across different types of parameters and also between fields
(see: :ref:`field-validation`). Graceful takes advantage of this fact and already
provides you with a small set of fully reusable validators that can be used to
validate both your parameters and serialization fields. For more details see
:any:`graceful.validators` module reference.



Handling multiple occurences of parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest way to allow user to specify multiple occurences of single
parameter is to use ``many`` keyword argument. It is available for every
base parameter class initialization and it is good practice to not override
this argument in custom parameter classes using custom initialization.

If ``many`` is set to ``True`` for given parameter the resulting ``params``
dictionary available in main method handlers of generic resources or through
``self.require_params(req)`` method will contain list of values for given
resource instead of single value.

For instance, if you are building some text search API and expect client
to provide multiple search string in single query you can describe your
basic API as follows:

.. code-block:: python

    from graceful.parameters import StringParam
    from graceful.resources.base import BaseResource

    class SearchResource(BaseResource):
        search = StringParam("text search string", many=True)


With such definition your client can provide list of multiple values for the
``search`` param using multiple instances of ``search=<value>`` in his query
string e.g::

    search=matt&search=damon&search=affleck

**Important:** if ``many`` is set to ``False`` the value stored under
corresponding key will  **always** represent the single parameter value. It is
important to note that providing multiple values for same parameter in the
query string by your API client is not considered an error even if parameter is
described as ``many=False``. In that case only one value will be included in
parameters dictionary and it is not defined which one. When documenting your
API you need to take special care when informing which parameter supports
muliple value and which not. You should also make sure to inform API users
of possibility of undefined behaviour when not following your instructions.



Order of values and ordered data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Remember that multiple values coming from parameter defined using ``many=True``
should be always considered independend from each other. This means that
**order of resulting parameter values is always undefined**.
If you need to handle parameters that represent specifically ordered list you
probably need custom parameter class that that will provide you with required
serialization. Such representation is generally independent from the ``many``
argument of such custom parameter class.

The reason for that design decision is because when order of data is important
then usually the order by itself represents is a named quality or entity.

The best way to undestand this is by example. For instance let's assume that
we are building some simple API that allows to search through some inventory
of clothes store. If we would like to allow clients to filter items by their
colors it completely makes sense to use following definition of query
parameter:


.. code-block:: python

    color = StringParam("One of main color items", many=True)


But if you are building some spatial search engine you might want to allow
user to search for data in region defined as a polygon. Polygon can be simply
represented by just an ordered list of points. But does it makes sense
to define your polygon as ``point`` parameter with ``many=True``? Probably not.
In case where order of data is important you need some custom parameter class
that will explicitely define how to handle such parameters. The naive
implementation for polygon parameter could be as follows:
The naive

.. code-block:: python

    from graceful.parameters import BaseParam

    class PolygonParam(BaseParam):
        """ Represents polygon parameter in string form of "x1,y1;x2,y2;..."
        """
        type = 'polygon'


        def value(self, raw_value):
            return [
                [float(x) for x in point.split(',')]
                for point in raw_value.split(';')
            ]



Such approach your will eventually make your code and API:

- Easier to understand - you will end up using parameter names that better
  explain what you and your API users are dealing with.
- Easier to document - parameter class can be inspected for the purpose of
  auto documentation. Their basic attributes (``type`` and ``spec``) are already
  included in default ``OPTIONS`` handler.
- Easier to extend - if you suddenly realize that you need to support multiple
  ordered sets of same type of data it is as simple as adding additional
  ``many=True`` to declaration of parameter that represents some data container



Custom containers
^^^^^^^^^^^^^^^^^

With the ``many=True`` option multiple values for the same parameter will be
returned as list. But sometimes you may want to do additional processing when
``many`` option is enables. For instance you may want to concatenate all
string searches to single string, make sure all values are unique or join
some ORM query sets using logical operator.

Of course it is completely valid approach to make such operation in your HTTP
method handler (in case of using :any:`BaseResource`) or in your specific
retrieval/update handler (in case of using generic resource classes). This is
usually very simple:


.. code-block:: python

    from graceful.parameters import StringParam
    from graceful.resources.generic import PaginatedListAPI


    class CatList(PaginatedListAPI):
        """
        List of all cats in our API
        """
        breed = StringParam(
            "set this param to filter cats by breed"
            many=True
        )

        def list(self, params, meta, **kwargs):
            unique_breeds = set(param['breed']
            ...

Unfortunately, when you have a lot of different parameters that need
similar handling (e.g. various ORM-specific filter objects) this can become
tedious and lead to excessive code duplication. The easiest way overcome this
problem is to use custom container handler for multiple parameter occurences.
This can be done in your custom parameter class by overriding its default
``container`` attribute.

The container handler can be both type object or a new method. It must accept
list of values as its single positional argument.

Following is an example :any:`StringParam` re-implementation which additionally
makes sure that multiple occurences of the same parameter are all unique.
Uniqueness is simply achieved by using built-in ``set`` type as its
``container`` attribute:


.. code-block:: python

    from graceful.parameters import BaseParam

    class UniqueStringParam(BaseParam):
        """Same as StringParam but on ``many=True`` returns set of values."""
        container = set


As already said, container handler can be a method too. This is very useful
for handling more complex use cases. For instance `solrq <http://solrq.readthedocs.io/en/latest/>`_
is a nice utility for creating `Apache Solr <http://lucene.apache.org/solr/>`_
search engine queries in Python. If your API somehow exposes Solr search it
would be nice to make parameter class that converts query string params
directly to ``solrq.Q`` objects. ``solrq`` allows also to easily join
multiple query objects using binary AND and OR operators in similar fashion
to Django's queryset filters:

.. code-block:: python

    >>> Q(text='cat') | Q(text='dog')
    <Q: text:cat OR text:dog>


It really makes sense to take advantage of such feature in your parameter
class that wraps GET params in ``solrq.Q`` instances whenever ``many=True``
option is enabled. Following is example of custom parameter class that allows
to collapse multiple values of search queries to single ``solrq.Q`` instance
with predefined operator:


.. code-block:: python

    from graceful.params import StringParam

    import operator
    from functools import reduce

    class FilterQueryParam(StringParam):
        """
        Param that represents Solr filter queries logically
        joined together depending on value of `op` argument
        """
        def __init__(
                self,
                details,
                solr_field,
                op=operator.and_,
                **kwargs
        ):
            if solr_field is None:
                raise ValueError(
                    "`solr_field` argument of {} cannot be None"
                    "".format(self.__class__.__name__)
                )

            self.solr_field = solr_field
            self.op = op

            super().__init__(details, **kwargs)

        def value(self, raw_value):
            return Q({self.solr_field: raw_value})

        def container(self, values):
            return reduce(self.op, values) if len(values) > 1 else values[0]


With such definition creating simple Solr-backed search API using graceful
and without extensive object serialization becomes pretty simple:


.. code-block:: python

    import operator

    from solrq import Value as V
    from pysolr import Solr
    from graceful.resources.generic import ListAPI
    from graceful.serializers import BaseSerializer

    solr = Solr()


    class VerbatimSerializer():
        """ Represents object as it is assuming that we deal with simple dicts
        """
        def to_representation(self, obj):
            return obj


    class Search(ListAPI):
        serializer = VerbatimSerializer()

        text = FilterQueryParam(
            "Basix text search argumment (many values => AND)",
            many=True,
            solr_field='text'
            default=V('*', safe=True)
        )

        category = StringParam(
            "set this param to filter cats by breed (many values => OR)"
            many=True,
            solr_field='category'
            default=V('*', safe=True),
            op=operator.or_,
        )

        def list(self, params, meta, **kwargs):
            return list(solr.search(params['text'] & params['category']))
