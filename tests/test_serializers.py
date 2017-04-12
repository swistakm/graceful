""" This module tests basic Serializer API behaviour.

All tested serializer classes should be defined within tests because
we test how whole framework for defining new serializers works.
"""
import pytest

from graceful.fields import BaseField, StringField
from graceful.serializers import BaseSerializer


class ExampleField(BaseField):
    """ This is basic field for usage in tests that has raw data representation
    (same as internal)
    """
    def from_representation(self, data):
        return data

    def to_representation(self, value):
        return value


def test_simple_serializer_definition(instance_class):
    """
    Test if serializers can be defined in declarative way
    """
    class TestSimpleSerializer(BaseSerializer):
        instance_factory = instance_class

        foo = ExampleField(
            details="first field for testing"
        )
        bar = ExampleField(
            details="second field for testing"
        )

    serializer = TestSimpleSerializer()
    # make sure there are only two fields
    assert isinstance(serializer.fields, dict)
    assert len(serializer.fields) == 2
    assert 'bar' in serializer.fields
    assert 'foo' in serializer.fields


def test_empty_serializer_definition(instance_class):
    """
    Make sure even empty serializer has the same interface
    """
    class TestEmptySerializer(BaseSerializer):
        instance_factory = instance_class
        pass

    serializer = TestEmptySerializer()
    assert isinstance(serializer.fields, dict)
    assert len(serializer.fields) == 0


def test_serializer_inheritance(instance_class):
    class TestParentSerializer(BaseSerializer):
        instance_factory = instance_class
        foo = ExampleField(
            details="first field for testing"
        )
        bar = ExampleField(
            details="second field for testing"
        )

    class TestDerivedSerializer(TestParentSerializer):
        instance_factory = instance_class
        baz = ExampleField(
            details="this is additional field added as an extension"
        )
        pass

    serializer = TestDerivedSerializer()
    # make sure there are only two fields
    assert isinstance(serializer.fields, dict)
    assert len(serializer.fields) == 3
    assert 'bar' in serializer.fields
    assert 'foo' in serializer.fields
    assert 'baz' in serializer.fields


def test_serializer_field_overriding(instance_class):
    """
    Test serializer fields can be overriden
    """
    override_label = "overriden"
    parent_label = "parent"

    class TestParentSerializer(BaseSerializer):
        instance_factory = instance_class

        foo = ExampleField(label=parent_label, details="parent foo field")
        bar = ExampleField(label=parent_label, details="parent bar field")

    class TestOverridingSerializer(TestParentSerializer):
        instance_factory = instance_class

        foo = ExampleField(label=override_label, details='overriden foo field')

    serializer = TestOverridingSerializer()
    # make sure there are only two fields
    assert len(serializer.fields) == 2
    assert 'bar' in serializer.fields
    assert 'foo' in serializer.fields

    assert serializer.fields['foo'].label == override_label
    assert serializer.fields['bar'].label == parent_label


def test_serializer_simple_representation(instance_class):
    class SomeConcreteSerializer(BaseSerializer):
        instance_factory = instance_class

        name = ExampleField(details="name of instance object")
        address = ExampleField(details="instance address")

    instance = instance_class(
        name="John",
        address="US",
        # note: gender is not included in serializer
        #   fields so it will be dropped
        gender="male",
    )

    serializer = SomeConcreteSerializer()

    # test creating representation
    representation = serializer.to_representation(instance)
    assert representation == {"name": "John", "address": "US"}

    # test recreating instance
    recreated = serializer.from_representation(representation)
    assert recreated == instance_class(name="John", address="US")


def test_serializer_sources_representation(instance_class):
    """
    Test representing objects with sources of fields different that their names
    """
    class SomeConcreteSerializer(BaseSerializer):
        instance_factory = instance_class

        name = ExampleField(
            details="name of instance object (taken from _name)",
            source="_name",
        )
        address = ExampleField(
            details="address of instace object (taken from _address)",
            source="_address"
        )

    instance = instance_class(
        _name="John",
        _address="US",
        # note: gender is not included in serializer
        #   fields so it will be dropped
        gender="male",
    )

    serializer = SomeConcreteSerializer()

    # test creating representation
    representation = serializer.to_representation(instance)
    assert representation == {"name": "John", "address": "US"}

    # test recreating instance
    recreated = serializer.from_representation(representation)
    assert recreated == instance_class(_name="John", _address="US")


def test_serializer_describe(instance_class):
    """ Test that serializers are self-describing
    """
    class ExampleSerializer(BaseSerializer):
        instance_factory = instance_class

        foo = ExampleField(label='foo', details='foo foo')
        bar = ExampleField(label='bar', details='bar bar')

    serializer = ExampleSerializer()

    description = serializer.describe()
    assert isinstance(description, dict)
    assert 'foo' in description
    assert 'bar' in description
    assert all([
        # note: 'label' and 'description' is a minimal set of description
        #       entries expected in each field
        'label' in field_description and 'details' in field_description
        for field_description in description.values()
    ])


def test_serializer_with_field_many(instance_class):
    class CaseSwitchField(BaseField):
        def to_representation(self, value):
            return value.upper()

        def from_representation(self, data):
            return data.lower()

    class ExampleSerializer(BaseSerializer):
        instance_factory = instance_class

        case_switch = CaseSwitchField(
            details='multiple values field', many=True
        )

    serializer = ExampleSerializer()

    # note: it can be any object type, not only a dictionary
    instance = instance_class(case_switch=["aa", "bb", "cc"])
    desired = {'case_switch': ["AA", "BB", "CC"]}

    assert serializer.to_representation(instance) == desired
    assert serializer.from_representation(desired) == instance

    with pytest.raises(ValueError):
        serializer.from_representation(
            {"case_switch": "definitely not a sequence"}
        )


def test_serializer_many_validation(instance_class):
    def is_upper(value):
        if value.upper() != value:
            raise ValueError("should be upper")

    class ExampleSerializer(BaseSerializer):
        instance_factory = instance_class

        up = StringField(
            details='multiple values field',
            many=True,
            validators=[is_upper]
        )

    invalid = {'up': ["aa", "bb", "cc"]}
    valid = {'up': ["AA", "BB", "CC"]}

    serializer = ExampleSerializer()

    with pytest.raises(ValueError):
        serializer.from_representation(invalid)

    serializer.from_representation(valid)
