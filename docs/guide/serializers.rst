Serializers and fields
----------------------

The purpose of serializers and fields is to describe how structured is data
that your API resources can return and accept. They together describe what
we could call a "resource representation".

They also helps binding this resource representation with internal objects
that you use in your application no matter what you have there - dicts, native,
class instances, ORM objects, documents, whatever.
There is only one requirement: there must be a way to represent them as a set
of independent fields and their values. In other words: dictionaries.

Example of simple serializer:

.. code-block:: python

    from graceful.serializers import BaseSerializer
    from graceful.fields import RawField, IntField, FloatField


    class CatSerializer(BaseSerializer):
        species = RawField("non normalized cat species")
        age = IntField("cat age in years")
        height = FloatField("cat height in cm")


Serializers are intended to be used with generic resources provided by
:any:`graceful.resources.generic` module so only handlers
for retrieving, updating,
creating etc. of objects from validated data is needed:

Functionally equivalent example using generic resources:

.. code-block:: python

    from graceful.resources.generic import RetrieveUpdateAPI
    from graceful.serializers import BaseSerializer
    from graceful.fields import RawField, FloatField

    class Cat(object):
        def __init__(self, name, height):
            self.name = name
            self.height = height

    class CatSerializer(BaseSerializer):
        name = RawField("name of a cat")
        height = FloatField("height in cm")

    class CatResource(RetrieveUpdateAPI):
        serializer = CatSerializer()

        def retrieve(self, params, meta, **kwargs):
            return Cat('molly', 30)

        def update(self, params, meta, validated, **kwargs):
            return Cat(**validated)

Anyway serializers can be used outside of generic resources but some additional
work need to be done then:

.. code-block:: python

    import falcon

    from graceful.resources.base import BaseResource

    class CatResource(BaseResource):
        serializer = CatSerializer()

        def on_get(self, req, resp, **kwargs):
            # this in probably should be read from storage
            cat = Cat('molly', 30)

            self.make_body(
                req, resp,
                meta={},
                content=self.serializer.to_representation(cat),
            )

        def on_put(self, req, resp, **kwargs)
            validated = self.require_validated(req)
            updated_cat = Cat(**validated)

            self.make_body(
                req, resp,
                meta={},
                # may be nothing or again representation of new cat
                content=self.serializer.to_representation(new_cat),
            )

            req.status = falcon.HTTP_CREATED



Field arguments
~~~~~~~~~~~~~~~


All field classes accept this set of arguments:

* **details** *(str, required)*: verbose description of field.

* **label** *(str, optional)*: human readable label for this
  field (it will be used for describing resource on OPTIONS requests).

  *Note that it is recomended to use field names that are self-explanatory
  intead of relying on param labels.*

* **source** *(str, optional)*: name of internal object key/attribute
  that will be passed to field's on ``.to_representation(value)`` call.
  Special ``'*'`` value is allowed that will pass whole object to
  field when making representation. If not set then default source will
  be a field name used as a serializer's attribute.

* **validators** *(list, optional)*: list of validator callables.

* **many** *(bool, optional)* set to True if field is in fact a list
  of given type objects


.. note::

   ``source='*'`` is in fact a dirty workaround and will not work well
   on validation when new object instances needs to be created/updated
   using POST/PUT requests. This works quite well with simple retrieve/list
   type resources but in more sophisticated cases it is better to use
   custom object properties as sources to encapsulate such fields.


Field validation
~~~~~~~~~~~~~~~~

Additional validation of field value can be added to each field as a list of
callables. Any callable that accepts single argument can be a validator but
in order to provide correct HTTP responses each validator shoud raise
:class:`graceful.errors.ValidationError` exception on validation call.

.. note::

   Concept of validation for fields is understood here as a process of checking
   if data of valid type (successfully parsed/processed by
   ``.from_representation`` handler) does meet some other constraints
   (lenght, bounds, unique, etc).


Example of simple validator usage:

.. code-block:: python

    from graceful.errors import ValidationError
    from graceful.serializers import BaseSerializer
    from graceful.fields import FloatField

    def tiny_validator(value):
        if value > 20.0:
            raise ValidationError


    class TinyCats(BaseSerializer):
        """ This resource accepts only cats that has height <= 20 cm """
        height = FloatField("cat height", validators=[tiny_validator])


graceful provides some small set of predefined validator helpers in
:any:`graceful.validators` module.


Custom fields
~~~~~~~~~~~~~

Custom field types can be created by subclassing of :class:`BaseField` class
and implementing of two method handlers:

* ``.from_representation(raw)``: returns internal data type from raw string
  provided in request
* ``.to_representation(data)``: returns representation of internal data type

Example of custom field that assumes that data in internal object is stored
as a serialized JSON string that we would like to (de)serialize:

.. code-block:: python

    import json

    from graceful.fields import BaseField


    class JSONField(BaseField):
        def from_representation(raw):
            return json.dumps(raw)

        def to_representation(data):
            return json.loads(data)

