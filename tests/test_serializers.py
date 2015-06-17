# -*- coding: utf-8 -*-
""" This module tests basic Serializer API behaviour.

All tested serializer classes should be defined within tests because
we test how whole framework for defining new serializers works.
"""
import pytest

from graceful.fields import BaseField
from graceful.serializers import BaseSerializer


class TestField(BaseField):
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
        foo = TestField(
            details="first field for testing"
        )
        bar = TestField(
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
        foo = TestField(
            details="first field for testing"
        )
        bar = TestField(
            details="second field for testing"
        )

    class TestDerivedSerializer(TestParentSerializer):
        baz = TestField(
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
        foo = TestField(label=parent_label, details="parent foo field")
        bar = TestField(label=parent_label, details="parent bar field")

    class TestOverridingSerializer(TestParentSerializer):
        foo = TestField(label=override_label, details='overriden foo field')

    serializer = TestOverridingSerializer()
    # make sure there are only two fields
    assert len(serializer.fields) == 2
    assert 'bar' in serializer.fields
    assert 'foo' in serializer.fields

    assert serializer.fields['foo'].label == override_label
    assert serializer.fields['bar'].label == parent_label


def test_serialiser_simple_representation():
    class SomeConcreteSerializer(BaseSerializer):
        name = TestField(details="name of instance object")
        address = TestField(details="instance address")

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
        name = TestField(
            details="name of instance object (taken from _name)",
            source="_name",
        )
        address = TestField(
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


def test_serializer_set_attribute():
    serializer = BaseSerializer()

    # test dict keys are treated as attributes
    instance = {}
    serializer.set_attribute(instance, 'foo', 'bar')
    assert instance == {'foo': 'bar'}

    # test normal objects atrributes are attributes indeed
    # in scope of this method
    class SomeObject():
        def __init__(self):
            self.foo = None

    instance = SomeObject()
    serializer.set_attribute(instance, 'foo', 'bar')
    assert instance.foo == 'bar'


def test_serializer_get_attribute():
    serializer = BaseSerializer()

    # test dict keys are treated as attributes
    instance = {'foo': 'bar'}
    assert serializer.get_attribute(instance, 'foo') == 'bar'

    # test normal objects atrributes are attributes indeed
    # in scope of this method
    class SomeObject():
        def __init__(self):
            self.foo = 'bar'

    instance = SomeObject()
    assert serializer.get_attribute(instance, 'foo') == 'bar'

    # test that getting non existent attribute returns None
    assert serializer.get_attribute(instance, 'nonexistens') is None


def test_serializer_source_wildcard():
    """
    Test that '*' wildcard causes whole instance is returned on get attribute
    :return:
    """
    serializer = BaseSerializer()

    instance = {"foo", "bar"}
    assert serializer.get_attribute(instance, '*') == instance


def test_serializer_source_field_with_wildcard():
    class ExampleSerializer(BaseSerializer):
        instance = TestField(
            details='whole object instance goes here',
            source='*',
        )

    serializer = ExampleSerializer()
    instance = {'foo', 'bar'}

    assert serializer.to_representation(instance)['instance'] == instance


def test_serializer_describe():
    """ Test that serializers are self-describing
    :return:
    """
    class ExampleSerializer(BaseSerializer):
        foo = TestField(label='foo', details='foo foo')
        bar = TestField(label='bar', details='bar bar')

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


def test_serialiser_representation_with_field_many():
    class UpperField(BaseField):
        def to_representation(self, value):
            return value.upper()

    class ExampleSerializer(BaseSerializer):
        up = UpperField(details='multiple values field', many=True)

    serializer = ExampleSerializer()
    instance = {'up': ["aa", "bb", "cc"]}

    assert serializer.to_representation(instance) == {"up": ["AA", "BB", "CC"]}
