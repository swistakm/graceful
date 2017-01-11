import re
import pytest

from graceful import validators


def test_min_validator():
    validator = validators.min_validator(10)

    assert validator(10) is None
    assert validator(12) is None
    assert validator(30) is None

    with pytest.raises(ValueError):
        validator(0)


def test_max_validator():
    validator = validators.max_validator(10)

    assert validator(10) is None
    assert validator(8) is None
    assert validator(-12) is None

    with pytest.raises(ValueError):
        validator(12)


@pytest.mark.parametrize("choices", [
    # test different kind of iterables as choices
    # * list
    [1, 2, 3, 4],
    # * set
    {1, 2, 3, 4},
    # * tuple
    (1, 2, 3, 4),
    # * dict
    {1: None, 2: None, 3: None, 4: None},
])
def test_choices_validator(choices):
    validator = validators.choices_validator(choices)

    assert validator(1) is None
    assert validator(2) is None
    assert validator(3) is None
    assert validator(4) is None

    with pytest.raises(ValueError):
        validator(12)


class ExampleOfAnythingMatchable(object):
    def __init__(self, excluded):
        self.excluded = excluded

    def match(self, value):
        return value != self.excluded

    @property
    def pattern(self):
        return "not " + self.excluded


@pytest.mark.parametrize("match", [
    # test diffetent matches:
    # * compiled re
    re.compile('\w+\d+'),
    # * string regexp
    '\w+\d+',
    # * just anything 'matchable'
    ExampleOfAnythingMatchable(excluded='bar'),
])
def test_match_validator(match):
    validator = validators.match_validator(match)

    assert validator('foo1980') is None
    with pytest.raises(ValueError):
        validator('bar')


def test_match_validator_invalid_match():
    with pytest.raises(TypeError):
        # floats is neither a string nor anything 'matchable'
        validators.match_validator(123123.123)
