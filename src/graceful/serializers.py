from collections import OrderedDict

from graceful.errors import DeserializationError
from graceful.fields import BaseField


class MetaSerializer(type):
    """Metaclass for handling serialization with field objects."""

    _fields_storage_key = '_fields'

    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        """Prepare class namespace in a way that ensures order of attributes.

        This needs to be an `OrderedDict` so `_get_fields()` method can
        construct fields storage that preserves the same order of fields as
        defined in code.

        Note: this is python3 thing and support for ordering of params in
        descriptions will not be backported to python2 even if this framework
        will get python2 support.

        """
        return OrderedDict()

    @classmethod
    def _get_fields(mcs, bases, namespace):
        """Create fields dictionary to be used in resource class namespace.

        Pop all field objects from attributes dict (namespace) and store them
        under _field_storage_key atrribute. Also collect all fields from base
        classes in order that ensures fields can be overriden.

        Args:
            bases: all base classes of created serializer class
            namespace (dict): namespace as dictionary of attributes

        """
        fields = [
            (name, namespace.pop(name))
            for name, attribute
            in list(namespace.items())
            if isinstance(attribute, BaseField)
        ]

        for base in reversed(bases):
            if hasattr(base, mcs._fields_storage_key):
                fields = list(
                    getattr(base, mcs._fields_storage_key).items()
                ) + fields

        return OrderedDict(fields)

    def __new__(mcs, name, bases, namespace):
        """Create new class object instance and alter its namespace."""
        namespace[mcs._fields_storage_key] = mcs._get_fields(bases, namespace)
        return super().__new__(
            # note: there is no need preserve order in namespace anymore so
            # we convert it explicitly to dict
            mcs, name, bases, dict(namespace)
        )


class BaseSerializer(metaclass=MetaSerializer):
    """Base serializer class for describing internal object serialization.

    Example:

    .. code-block:: python

        from graceful.serializers import BaseSerializer
        from graceful.fields import RawField, IntField, FloatField


        class CatSerializer(BaseSerializer):
            species = RawField("non normalized cat species")
            age = IntField("cat age in years")
            height = FloatField("cat height in cm")

    """

    #: Allows to override instance object constructon with custom type
    #: like defaultdict, SimpleNamespace or database model class.
    instance_factory = dict

    @property
    def fields(self):
        """Return dictionary of field definition objects of this serializer."""
        return getattr(self, self.__class__._fields_storage_key)

    def to_representation(self, instance):
        """Convert given internal object instance into representation dict.

        Representation dict may be later serialized to the content-type
        of choice in the resource HTTP method handler.

        This loops over all fields and retrieves source keys/attributes as
        field values with respect to optional field sources and converts each
        one using ``field.to_representation()`` method.

        Args:
            instance (object): internal object that needs to be represented

        Returns:
            dict: representation dictionary

        """
        # note: representations does not have their custom facotries like
        #       instances because they as only used during content-type
        #       serialization and deserialization and cannot be manipulated
        #       inside of resource classes.
        representation = {}

        for name, field in self.fields.items():
            # note: fields do not know their names in source representation
            #        but may know what attribute they target from instance
            attribute = field.read_instance(instance, field.source or name)

            if attribute is None:
                # Skip none attributes so fields do not have to deal with them
                field.update_representation(
                    representation, name, [] if field.many else None
                )

            elif field.many:
                field.update_representation(
                    representation, name, [
                        field.to_representation(item) for item in attribute
                    ]
                )
            else:
                field.update_representation(
                    representation, name, field.to_representation(attribute)
                )

        return representation

    def from_representation(self, representation, partial=False):
        """Convert given representation dict into internal object.

        Internal object is simply a dictionary of values with respect to field
        sources. This method does not quit on first failure to make sure that
        as many as possible issues will be presented to the client.

        Args:
           representation (dict): dictionary with field representation values

        Raises:
            DeserializationError: when at least of these issues occurs:

                * if at least one of representation field is not formed as
                  expected by the field object (``ValueError`` raised by
                  field's ``from_representation()`` method).
                * if ``partial=False`` and at least one representation fields
                  is missing.
                * if any non-existing or non-writable field is provided in
                  representation.
                * if any custom field validator fails (raises
                  ``ValidationError`` or ``ValueError`` exception)

            ValidationError: on custom user validation checks implemented with
                ``validate()`` handler.

        """
        instance = self.instance_factory()

        failed = {}
        invalid = {}

        # note: we need to perform validation on whole representation before
        #       validation because there is no
        missing, forbidden = self._validate_representation(
            representation, partial
        )

        for name, field in self.fields.items():
            if name not in representation:
                continue

            try:
                raw_entry = field.read_representation(representation, name)
                if (
                    # note: we cannot check for any sequence or iterable
                    #       because of strings and nested dicts.
                    not isinstance(raw_entry, (list, tuple)) and
                    field.many
                ):
                    raise ValueError("field should be sequence")

                field_values = [
                    field.from_representation(item)
                    for item in ([raw_entry] if not field.many else raw_entry)
                ]

                for value in field_values:
                    field.validate(value)

                field.update_instance(
                    instance,
                    # If field does not have explicit source string then use
                    # its name.
                    field.source or name,
                    # many=True fields require special care
                    field_values if field.many else field_values[0]
                )

            except ValueError as err:
                failed[name] = str(err)

        if any([missing, forbidden, invalid, failed]):
            raise DeserializationError(missing, forbidden, invalid, failed)

        # note: expected to raise ValidationError. It is extra feature handle
        #       so we dont try hard to merge wit previous errors.
        self.validate(instance, partial)

        return instance

    def _validate_representation(self, representation, partial=False):
        """Validate resource representation fieldwise.

        Check if object has all required fields to support full or partial
        object modification/creation and ensure it does not contain any
        forbidden fields.

        Returns:

            A ``(missing, forbidden)`` tuple with lists indicating fields that
            failed validation.
        """
        missing = [
            name for name, field in self.fields.items()
            if all((
                not partial,
                name not in representation,
                not field.read_only
            ))
        ]

        forbidden = [
            name for name in representation
            if name not in self.fields or self.fields[name].read_only
        ]

        return missing, forbidden

    def validate(self, instance, partial=False):
        """Validate given internal object.

        Internal object is a dictionary that have sucesfully passed general
        validation against missing/forbidden fields and was checked with
        per-field custom validators.

        Args:
            instance (dict): internal object instance to be validated.
            partial (bool): if set to True then incomplete instance
              is accepted (e.g. on PATCH requests) so it is possible that
              not every field is available.

        Raises:
            ValidationError: raised when deserialized object does not meet some
                user-defined contraints.
        """

    def describe(self):
        """Describe all serialized fields.

        It returns dictionary of all fields description defined for this
        serializer using their own ``describe()`` methods with respect to order
        in which they are defined as class attributes.

        Returns:
            OrderedDict: serializer description

        """
        return OrderedDict([
            (name, field.describe())
            for name, field in self.fields.items()
        ])
