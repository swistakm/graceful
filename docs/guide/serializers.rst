Serializers and fields
----------------------

The purpose of serializers and fields is to describe how structured is data
that your API resources can return and accept. They together describe what
we could call a "resource representation".

They also helps binding this resource representation with internal objects
that you use in your application no matter what you have there - native python
data types, ORM objects, documents, whatever. There is only one requirement:
there must be a way to represent them as a set of independent fields and their
values. In other words: dictionaries.

Example of simple serializer:

.. code-block:: python

    from graceful.serializers import BaseSerializer
    from graceful.fields import RawField, IntField, FloatField


    class CatSerializer(BaseSerializer):
        species = RawField("non normalized cat species")
        age = IntField("cat age in years")
        height = FloatField("cat height in cm")


Serializers
~~~~~~~~~~~

.. todo:: describe method handlers and custom serializers



Field arguments
~~~~~~~~~~~~~~~


All param classes accept this set of arguments:

* ``details`` (required) - verbose description of field.

* ``label`` (defaults to *None*) - human readable label for this
  field (it will be used for describing resource on OPTIONS requests).

  *Note that it is recomended to use field names that are self-explanatory
  intead of relying on param labels.*

* ``source`` (defaults to *None*) - name of internal object key/attribute
  that will be passed to field's on ``.to_representation(value)`` call.
  Special ``'*'`` is value allowed that will pass whole object to
  ``.to_representation(value)``. If set to *None* then default source will
  be a field name used as a serializers attribute.

* ``validators`` - list of validator callables.

* ``many`` (defualts to *False*) - set to True if field is in fact a list
  of given type objects


Field validation
~~~~~~~~~~~~~~~~

Additional validation of field value can be added to each field as a list of
callables. Any callable that accepts single argument can be a validator but
in order to provide correct HTTP responses each validator shoud raise
:any:`graceful.validators.ValidationError` exception on validation call.

.. note::

   Concept of validation for fields is understood here as a process of checking
   if data of valid type (successfully parsed/processed by
   ``.from_representation`` handler) does meet some other constraints
   (lenght, bounds, unique, etc).


Example of simple validator usage:

.. code-block:: python

    from graceful.validators import ValidationError
    from graceful.serializers import BaseSerializer
    from graceful.fields import FloatField

    def tiny_validator(value):
        if value > 20.0:
            raise ValidationError


    class TinyCats(BaseSerializer):
        """ This resource accepts only cats that has height <= 20 cm """
        height = FloatField("cat height", validators=[tiny_validator])


``graceful`` provides some small set of predefined validators in
:any:`graceful.validators` module.


Custom fields
~~~~~~~~~~~~~

Custom field types can be created by subclassing of :class:`BaseField` class
and implementing of two method handlers:

* ``.from_representation(raw)`` - returns internal data type from raw string
  provided in request
* ``.to_representation(data)`` - returns representation of internal data type

Example of custom field that assumes that data in internal object is stored
as a serialized JSON string that we would like to deserialize:

.. code-block:: python

    import json

    from graceful.fields import BaseField


    class JSONField(BaseField):
        def from_representation(raw):
            return json.dumps(raw)

        def to_representation(data):
            return json.loads(data)

