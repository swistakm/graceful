# -*- coding: utf-8 -*-
import re

__all__ = [
    'min_validator',
    'max_validator',
    'choices_validator',
]


class ValidationError(ValueError):
    pass


def min_validator(min_value):
    def validator(value):
        if value < min_value:
            raise ValidationError("{} is not >= {}".format(value, min_value))

    return validator


def max_validator(max_value):
    def validator(value):
        if value > max_value:
            raise ValidationError("{} is not <= {}".format(value, max_value))

    return validator


def choices_validator(choices):
    def validator(value):
        if value not in choices:
            # note: make it a list for consistent representation
            raise ValidationError(
                "{} is not in {}".format(value, list(choices))
            )

    return validator


def match_validator(match):
    if isinstance(match, str):
        compiled = re.compile(match)
    elif hasattr(match, 'match'):
        # check it early so we could say something is wrong early
        compiled = match
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
