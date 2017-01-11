import pytest
from graceful.errors import ValidationError

from graceful.fields import (
    BaseField,
    RawField,
    StringField,
    IntField,
    FloatField,
    BoolField,
)


def test_base_field_implementation_hooks():
    field = BaseField(None)

    with pytest.raises(NotImplementedError):
        field.to_representation(None)

    with pytest.raises(NotImplementedError):
        field.from_representation(None)


def test_base_field_describe():
    class SomeField(BaseField):
        type = "anything"
        spec = None

    field = SomeField(label="foo", details="bar")

    assert field.describe() == {
        'label': "foo",
        'details': "bar",
        'type': "anything",
        'spec': None,
        'read_only': False
    }

    # test extending descriptions by call with kwargs
    assert 'baz' in field.describe(baz="baz")


def test_base_field_validate():
    def always_pass_validator(value):
        pass

    def always_raise_validator(value):
        raise ValidationError("Just because!")

    # here there is no chance to validate
    field_with_picky_validation = BaseField(
        "test base field validators",
        validators=[always_pass_validator, always_raise_validator]
    )
    with pytest.raises(ValidationError):
        field_with_picky_validation.validate("foo")

    # here will validate because of very indulgent validation
    field_with_lenient_validation = BaseField(
        "test validate",
        validators=[always_pass_validator]
    )
    field_with_lenient_validation.validate("foo")

    # here will also validate because there are no vaidators
    field_with_lenient_validation = BaseField("test validate")
    field_with_lenient_validation.validate("foo")


# test on bunch of simple data types
@pytest.mark.parametrize('data_type', [int, float, str, dict, tuple, set])
def test_raw_field(data_type):
    field = RawField(None, None)

    instance = data_type()

    representation = field.to_representation(instance)
    assert isinstance(representation, data_type)
    assert instance == representation

    recreated = field.from_representation(representation)
    assert isinstance(recreated, data_type)
    assert instance == recreated


def test_string_field():
    field = StringField("test str field")

    assert field.to_representation("foo") == "foo"
    assert field.to_representation(123) == "123"

    assert field.from_representation("foo") == "foo"
    assert field.from_representation(123) == "123"


def test_int_field():
    field = IntField("test int field", max_value=100, min_value=0)

    # note: constraints (validators) does not affect conversions
    # between internal value and representation and this is fine
    # because we need to have value converted from representation
    # to be able to do validation
    assert field.from_representation(123) == 123
    assert field.from_representation('123') == 123
    assert field.to_representation(123) == 123
    assert field.to_representation('123') == 123

    # accept only explicit integers
    with pytest.raises(ValueError):
        field.to_representation('123.0213')
    with pytest.raises(ValueError):
        field.from_representation('123.0213')

    # accept only numbers
    with pytest.raises(ValueError):
        field.to_representation('foo')
    with pytest.raises(ValueError):
        field.from_representation('foo')

    # test validation
    with pytest.raises(ValidationError):
        field.validate(-10)
    with pytest.raises(ValidationError):
        field.validate(123)


def test_bool_field():
    field = BoolField("test bool field")

    # note: this both checks also ensures that accepted representations do
    # not overlap
    for representation in BoolField._FALSE_VALUES:
        assert field.from_representation(representation) is False
    for representation in BoolField._TRUE_VALUES:
        assert field.from_representation(representation) is True

    assert field.to_representation(True) is True
    assert field.to_representation(False) is False

    with pytest.raises(ValueError):
        field.from_representation('foobar')


def test_bool_field_custom_representations():
    field = BoolField("test bool field", representations=('foo', 'bar'))

    assert field.from_representation('foo') is False
    assert field.from_representation('bar') is True

    assert field.to_representation(False) == 'foo'
    assert field.to_representation(True) == 'bar'


def test_float_field():
    field = FloatField("test int field", max_value=100.0, min_value=0.0)

    # note: constraints (validators) does not affect conversions
    # between internal value and representation and this is fine
    # because we need to have value converted from representation
    # to be able to do validation
    assert isinstance(field.from_representation(123), float)
    assert isinstance(field.from_representation('123'), float)
    assert isinstance(field.to_representation(123), float)
    assert isinstance(field.to_representation('123'), float)

    # accept only numbers
    with pytest.raises(ValueError):
        field.to_representation('foo')
    with pytest.raises(ValueError):
        field.from_representation('foo')

    # check validation
    with pytest.raises(ValidationError):
        field.validate(-10)
    with pytest.raises(ValidationError):
        field.validate(123)
