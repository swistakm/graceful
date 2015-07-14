Parameters
----------

Parameters provide a way to describe and evaluate all request qeury params
that can be used in your API resources.

New parameters are added to resources as class attributes:

.. code-block:: python

    from graceful.parameters import StringParam, IntParam
    from graceful.resources.base import BaseResource

    class SomeResource(BaseResource):
        filter_by_name = StringParam("Filter resource instances by their name")
        depth = IntParam("Set depth of something")


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
                "'{code}' is not valid alpha2 language code".format(
                    code=raw_value)
            )
