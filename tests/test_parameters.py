# -*- coding: utf-8 -*-
import decimal
import base64

import pytest

from graceful.parameters import (
    BaseParam,
    StringParam,
    Base64EncodedParam,
    IntParam,
    FloatParam,
    DecimalParam,
    BoolParam,
)


class TestParam(BaseParam):
    """Example testing param class that returns raw value
    """
    type = "string"
    rfc = (
        "example spec",
        "http://example.com",
    )

    def value(self, raw_value):
        return raw_value


def test_parameter_description():
    param = TestParam(details="details", required=False)

    description = param.describe()
    assert 'label' in description
    assert 'details' in description
    assert 'required' in description
    assert 'spec' in description
    assert 'type' in description


def test_parameter_value():
    param = TestParam('label', "details", required=False)
    value = "something passed in qs"

    # simple API existence check
    # basic Parameter object is only a descriptive layer that passes same
    # value without any conversion
    assert param.value(value) == value


def test_implementation_hooks():
    param = BaseParam(details='details')

    with pytest.raises(NotImplementedError):
        param.value("something")


def test_param_default_value():
    # this should pass
    TestParam(details="details", default="foo")

    # anything other than str should raise TypeError
    with pytest.raises(TypeError):
        TestParam(details="details", default=123)

    # test using required and default at the same time has no sense
    with pytest.raises(ValueError):
        TestParam(details="details", default="foo", required=True)


def test_string_param():
    param = StringParam(details="stringy stringy")
    assert param.value("foo") == "foo"


def _test_param(param, encoded, invalid, desired):
    """
    Perform basic param test.

    * check if decoded value is same as desired
    * check if decoding invalid value raises ValueError

    :param param: param object
    :param encoded:
    :param invalid:
    :param desired: desired value after value desi
    :return:
    """
    assert param.value(encoded) == desired

    with pytest.raises(ValueError):
        param.value(invalid)


def test_base64_param():
    param = Base64EncodedParam(details='encoded param')
    # some value to test
    value = "foobar"
    # param will always get unicode string to its value since this what
    # sits inside of falcon param
    encoded = base64.b64encode(bytes(value, 'utf-8')).decode('utf-8')

    # note: "123" is not valid base64 encoded string
    _test_param(param, encoded, "123", value)


def test_int_param():
    param = IntParam(details="count of something")

    _test_param(param, '123', 'aaa', 123)


def test_float_param():
    param = FloatParam(details="details")

    _test_param(param, '123.0', 'aaa', 123.0)


def test_decimal_param():
    param = DecimalParam(details="some decimal field")

    _test_param(param, '123.123', 'aaa', decimal.Decimal("123.123"))


@pytest.mark.parametrize('encoded, desired', (
    ('True', True),
    ('TRUE', True),
    ('1', True),
    ('False', False),
    ('FALSE', False),
    ('0', False),
    ('0.0', False),
))
def test_bool_param(encoded, desired):
    param = BoolParam(details="some bool field")

    assert param.value(encoded) == desired
