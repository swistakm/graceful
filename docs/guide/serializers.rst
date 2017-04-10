.. _guide-serializers:

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

* **details** *(str, required):* verbose description of field.

* **label** *(str, optional):* human readable label for this
  field (it will be used for describing resource on OPTIONS requests).

  *Note that it is recomended to use field names that are self-explanatory
  intead of relying on param labels.*

* **source** *(str, optional):* name of internal object key/attribute
  that will be passed to field's on ``.to_representation(value)`` call. If not
  set then default source is a field name used as a serializer's attribute.

* **validators** *(list, optional):* list of validator callables.

* **many** *(bool, optional):* set to True if field is in fact a list
  of given type objects

* **read_only** *(bool):* True if field is read-only and cannot be set/modified
  via POST, PUT, or PATCH requests.

* **write_only** *(bool):* True if field is write-only and cannot be retrieved
  via GET requests.

.. versionchanged:: 1.0.0

   Fields no no longer have special case treatment for ``source='*'`` argument.
   If you want to access multiple object keys and values within single
   serializer field please refer to :ref:`guide-field-attribute-access` section
   of this document.

.. _field-validation:

Field validation
~~~~~~~~~~~~~~~~

Additional validation of field value can be added to each field as a list of
callables. Any callable that accepts single argument can be a validator but
in order to provide correct HTTP responses each validator shoud raise
:class:`graceful.errors.ValidationError` exception on validation call.

.. note::

   Concept of validation for fields is understood here as a process of checking
   if data of valid type (i.e. data that was successfully parsed/processed by
   ``.from_representation()`` handler) does meet some other constraints
   (lenght, bounds, uniquess, etc).


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


Resource validation
~~~~~~~~~~~~~~~~~~~

In most cases field level validation is all that you need but sometimes you
need to perfom validation on whole resource representation or deserialized
object. It is possible to access multiple fields that were already deserialized
and pre-validated directly from serializer class.

You can provide your own object-level serialization handler using serializer's
``validate()`` method. This method accepts two arguments:

* **object_dict** *(dict):* it is deserialized object dictionary that already
  passed validation. Field sources instead of their representation names are
  used as its keys.

* **partial** *(bool):* it is set to ``True`` only on partial object updates
  (e.g. on ``PATCH`` requests). If you plan to support partial resource
  modification you should check this field and verify if you object has
  all the existing keys.

If your validation fails you should raise the
:class:`graceful.errors.ValidationError` exception. Following is the example
of resource serializer with custom object-level validation:


.. code-block:: python

    class DrinkSerializer():
        alcohol = StringField("main ingredient")
        mixed_with = StringField("what makes it tasty")

        def validate(self, object_dict, partial):
            # note: always make sure to call super `validate_object()`
            # to make sure that per-field validation is enabled.

            if partial and any([
                'alcohol' in object_dict,
                'mixed_with' in object_dict,
            ]):
                raise ValidationError(
                    "bartender refused to change ingredients"
                )

            # here is a place for your own validation
            if (
                object_dict['alcohol'] == 'whisky' and
                object_dict['mixed_with'] == 'cola'
            ):
                raise ValidationError(
                    "bartender refused to mix whisky with cola!"
                )


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

.. _guide-field-attribute-access:


Accessing multiple fields at once
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes you need to access multiple fields of internal object instance at
once in order to properly represent data in your API. This is very common when
interacting with legacy services/components that cannot be changed or when
your storage engine simply does not allow to store nested or structured objects.

Serializers generally work on per-field basis and allow only to translate field
names between representation and application internal objects. In order to
manipulate multiple representation or internal object instance keys within the
single field you need to create custom field class and override one or more
of following methods:

* ``read_instance(self, instance, key_or_attribute)``: read value from the
  object instance before serialization. The return value will be later passed
  as an argument to ``to_representation()`` method. The ``key_or_attribute``
  argument is field's name or source (if ``source`` explicitly specified).
  Base implementation defaults to dictionary key lookup or object attribute
  lookup.
* ``read_representation(self, representation, key_or_attribute)``: read value
  from the object instance before deserialization. The return value will be
  later passed as an argument to ``from_representation()`` method. The
  ``key_or_attribute`` argument the field's name. Base implementation defaults
  to dictionary key lookup or object attribute lookup.
* ``update_instance(self, instance, key_or_attribute, value)``: update the
  content of object instance after deserialization. The ``value`` argument is
  the return value of ``from_representation()`` method. The
  ``key_or_attribute`` argument the field's name or source (if ``source``
  explicitly specified). Base implementation defaults to dictionary key
  assignment or object attribute assignment.
* ``update_representation(self, representation, key_or_attribute, value)``:
  update the content of representation instance after serialization.
  The ``value`` argument is the return value of ``to_representation()`` method.
  The ``key_or_attribute`` argument the field's name. Base implementation
  defaults to dictionary key assignment or object attribute assignment.

To better explain how to use these methods let's assume that due to some
storage backend constraints we cannot save nested dictionaries. All of fields
of some nested object will have to be stored under separate keys but we still
want to present this to the user as separate nested dictionary. And of course
we want to support both writes and saves.

.. code-block:: python

    class OwnerField(RawField):
        def from_representation(self, data):
            if not isinstance(data, dict):
                raise ValueError("expected object")

            return {
                'owner_name': data.get('name'),
                'owner_age': data.get('age'),
            }

        def to_representation(self, value):
            return {
                'age': value.get('owner_age'),
                'name': value.get('owner_name'),
            }

        def validate(self, value):
            print(value)
            if 'owner_age' not in value or not isinstance(value['owner_age'], int):
                raise ValidationError("invalid owner age")

            if 'owner_name' not in value:
                raise ValidationError("invalid owner name")

        def update_instance(self, instance, attribute_or_key, value):
            # we assume that instance is always a dictionary so we can
            # use the .update() method
            instance.update(value)

        def read_instance(self, instance, attribute_or_key):
            # .to_representation() method requires acces to whole object
            # dictionary so we have to return whole object.
            return instance


Similar approach may be used to flatten nested objects into more compact
representations.
