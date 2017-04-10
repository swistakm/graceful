""" This module tests basic Serializer API behaviour.

All tested serializer classes should be defined within tests because
we test how whole framework for defining new serializers works.
"""
import pytest

import graceful
from graceful.errors import DeserializationError
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


def test_simple_serializer_definition():
    """
    Test if serializers can be defined in declarative way
    """
    class TestSimpleSerializer(BaseSerializer):
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


def test_empty_serializer_definition():
    """
    Make sure even empty serializer has the same interface
    """
    class TestEmptySerializer(BaseSerializer):
        pass

    serializer = TestEmptySerializer()
    assert isinstance(serializer.fields, dict)
    assert len(serializer.fields) == 0


def test_serializer_inheritance():
    class TestParentSerializer(BaseSerializer):
        foo = ExampleField(
            details="first field for testing"
        )
        bar = ExampleField(
            details="second field for testing"
        )

    class TestDerivedSerializer(TestParentSerializer):
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


def test_serializer_field_overriding():
    """
    Test serializer fields can be overriden
    """
    override_label = "overriden"
    parent_label = "parent"

    class TestParentSerializer(BaseSerializer):
        foo = ExampleField(label=parent_label, details="parent foo field")
        bar = ExampleField(label=parent_label, details="parent bar field")

    class TestOverridingSerializer(TestParentSerializer):
        foo = ExampleField(label=override_label, details='overriden foo field')

    serializer = TestOverridingSerializer()
    # make sure there are only two fields
    assert len(serializer.fields) == 2
    assert 'bar' in serializer.fields
    assert 'foo' in serializer.fields

    assert serializer.fields['foo'].label == override_label
    assert serializer.fields['bar'].label == parent_label


def test_serialiser_simple_representation():
    class SomeConcreteSerializer(BaseSerializer):
        name = ExampleField(details="name of instance object")
        address = ExampleField(details="instance address")

    object_instance = {
        "name": "John",
        "address": "US",
        # note: gender is not included in serializer
        #   fields so it will be dropped
        "gender": "male",
    }

    serializer = SomeConcreteSerializer()

    # test creating representation
    representation = serializer.to_representation(object_instance)
    assert representation == {"name": "John", "address": "US"}

    # test recreating instance
    recreated = serializer.from_representation(representation)
    assert recreated == {"name": "John", "address": "US"}


def test_serialiser_sources_representation():
    """
    Test representing objects with sources of fields different that their names
    """

    class SomeConcreteSerializer(BaseSerializer):
        name = ExampleField(
            details="name of instance object (taken from _name)",
            source="_name",
        )
        address = ExampleField(
            details="address of instace object (taken from _address)",
            source="_address"
        )

    object_instance = {
        "_name": "John",
        "_address": "US",
        # note: gender is not included in serializer
        #   fields so it will be dropped
        "gender": "male",
    }

    serializer = SomeConcreteSerializer()

    # test creating representation
    representation = serializer.to_representation(object_instance)
    assert representation == {"name": "John", "address": "US"}

    # test recreating instance
    recreated = serializer.from_representation(representation)
    assert recreated == {"_name": "John", "_address": "US"}


def test_serializer_read_only_write_only_serialization():
    class ExampleSerializer(BaseSerializer):
        readonly = ExampleField('A read-only field', read_only=True)
        writeonly = ExampleField('A write-only field', write_only=True)

    serializer = ExampleSerializer()

    assert serializer.to_representation(
        {"writeonly": "foo", 'readonly': 'bar'}
    ) == {"readonly": "bar"}


def test_serializer_read_only_write_only_deserialization():
    class ExampleSerializer(BaseSerializer):
        readonly = ExampleField('A read-only field', read_only=True)
        writeonly = ExampleField('A write-only field', write_only=True)

    serializer = ExampleSerializer()

    serializer.from_representation({"writeonly": "x"}) == {"writeonly": "x"}

    with pytest.raises(DeserializationError):
        serializer.from_representation({"writeonly": "x", 'readonly': 'x'})

    with pytest.raises(DeserializationError):
        serializer.from_representation({'readonly': 'x'})


def test_serializer_describe():
    """ Test that serializers are self-describing
    """
    class ExampleSerializer(BaseSerializer):
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


def test_serialiser_with_field_many():
    class UpperField(BaseField):
        def to_representation(self, value):
            return value.upper()

        def from_representation(self, data):
            return data.upper()

    class ExampleSerializer(BaseSerializer):
        up = UpperField(details='multiple values field', many=True)

    serializer = ExampleSerializer()
    obj = {'up': ["aa", "bb", "cc"]}
    desired = {'up': ["AA", "BB", "CC"]}

    assert serializer.to_representation(obj) == desired
    assert serializer.from_representation(obj) == desired

    with pytest.raises(ValueError):
        serializer.from_representation({"up": "definitely not a sequence"})


def test_serializer_many_validation():
    def is_upper(value):
        if value.upper() != value:
            raise ValueError("should be upper")

    class ExampleSerializer(BaseSerializer):
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
