# -*- coding: utf-8 -*-
import re

from graceful.errors import ValidationError


__all__ = [
    'min_validator',
    'max_validator',
    'choices_validator',
]


def min_validator(min_value):
    """
    Return validator function that will check internal value with
    ``value >= min_value`` check

    Args:
        min_value: minimal value for new validator

    """
    def validator(value):
        if value < min_value:
            raise ValidationError("{} is not >= {}".format(value, min_value))

    return validator


def max_validator(max_value):
    """
    Return validator function that will check if ``value >= min_value``.

    Args:
        max_value: maximum value for new validator

    """
    def validator(value):
        if value > max_value:
            raise ValidationError("{} is not <= {}".format(value, max_value))

    return validator


def choices_validator(choices):
    """
    Return validator function that will check if ``value in choices``.

    Args:
        max_value (list, set, tuple): allowed choices for new validator

    """
    def validator(value):
        if value not in choices:
            # note: make it a list for consistent representation
            raise ValidationError(
                "{} is not in {}".format(value, list(choices))
            )

    return validator


def match_validator(expression):
    """
    Return validator function that will check if matches given match.

    Args:
        match: if string then this will be converted to regular expression
           using ``re.compile``. Can be also any object that has ``match()`
           method like already compiled regular regular expression or custom
           matching object/class.

    """

    if isinstance(expression, str):
        compiled = re.compile(expression)
    elif hasattr(expression, 'match'):
        # check it early so we could say something is wrong early
        compiled = expression
    else:
        raise TypeError(
            'Provided match is nor a string nor has a match method '
            '(like re expressions)'
        )

    def validator(value):
        if not compiled.match(value):
            # note: make it a list for consistent representation
            raise ValidationError(
                "{} does not match pattern: {}".format(
                    value,
                    compiled.pattern
                    if hasattr(compiled, 'pattern')
                    else compiled
                )
            )

    return validator
