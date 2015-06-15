# -*- coding: utf-8 -*-
from graceful.validators import min_validator, max_validator


class BaseField(object):
    spec = None
    type = None

    def __init__(
            self,
            details,
            label=None,
            source=None,
            validators=None,
            many=False,
    ):
        """
        Base field class for subclassing. To create new field type
        subclass `BaseField` and implement following methods:

        * `from_representation()` - converts representation (used in
            request/response body) to internal value.
        * `to_representation()` - converts internal value to representation
           that will be used in response body.

        Example:

            class BoolField(BaseField):
                def from_representation(self, data):
                    if data in {'true', 'True', 'yes', '1', 'Y'}:
                        return True:
                    elif data in {'false', 'False', 'no', '0', 'N'}:
                        return False:
                    else:
                        raise ValueError(
                            "{data} is not valid boolean field".format(
                                data=data
                            )
                        )

                def to_representation(self, value):
                    return ["True", "False"][value]

        :param details: human readable description of field (it will be used
            for describing resource on OPTIONS requests).
        :param label: human readable label of a field (it will be used for
            describing resource on OPTIONS requests).
            Note: it is recommended to use field names that are
            self-explanatory intead of relying on field labels.
        :param source: source of representation object/attribute that will be
            passed to field. Special '*' value allowed that will pass whole
            object to field.
        :param validators: list of validator callables.
        """
        self.label = label
        self.source = source
        self.details = details
        self.validators = validators or []
        self.many = many

    def from_representation(self, data):
        raise NotImplementedError(
            "{cls}.from_representation() method not implemented".format(
                cls=self.__class__.__name__
            )
        )

    def to_representation(self, value):
        raise NotImplementedError(
            "{cls}.to_representation() method not implemented".format(
                cls=self.__class__.__name__
            )
        )

    def describe(self, **kwargs):
        """
        Describe serializer field for purpose of self documentation.

        Additional description on derrived resource class can be added using
        keyword arguments and calling super().decribe() method call
        like following:

             class SomeField(BaseField):
                 def describe(self, **kwargs):
                     return super(SomeField, self).describe(
                         type='list', **kwargs
                      )

        :param kwargs: dict of additional parameters for extending field's
            description
        :return: dict
        """
        description = {
            'label': self.label,
            'details': self.details,
            'type': "list of {}".format(self.type) if self.many else self.type,
            'spec': self.spec,
        }
        description.update(kwargs)
        return description

    def validate(self, value):
        """ Perform validation on value by running all field validators.
        Validator is a callable that accepts one positional argument and
        raises "ValidationError" when validation does not succeed.

        :param value:
        :return: None
        """
        for validator in self.validators:
            validator(value)


class RawField(BaseField):
    type = 'string'

    def from_representation(self, data):
        return data

    def to_representation(self, value):
        return value


class BoolField(BaseField):
    type = 'bool'

    _TRUE_VALUES = {'True', 'true', 'TRUE', 'T', 't', '1', 1, True}
    _FALSE_VALUES = {'False', 'false', 'FALSE', 'F', 'f' '0', 0, 0.0, False}

    _DEFAULT_REPRESENTATIONS = (False, True)

    def __init__(
            self,
            details,
            representations=None,
            **kwargs
    ):
        super(BoolField, self).__init__(details, **kwargs)

        if representations:
            # could not resist...
            self._FALSE_VALUES = {representations[False]}
            self._TRUE_VALUES = {representations[True]}

        self.representations = representations or self._DEFAULT_REPRESENTATIONS

    def from_representation(self, data):
        if data in self._TRUE_VALUES:
            return True
        elif data in self._FALSE_VALUES:
            return False
        else:
            raise ValueError(
                "{type} type value must be one of {{values}}".format(
                    type=self.type,
                    values=self._TRUE_VALUES.union(self._FALSE_VALUES)
                )
            )

    def to_representation(self, value):
        return self.representations[value]


class IntField(BaseField):
    type = 'int'

    def __init__(
            self,
            details,
            max_value=None,
            min_value=None,
            **kwargs
    ):
        """
        :param max_value: max accepted value. Will cause ValidationError
           exception when value greater than `max_value` passed during
           validation
        :param min_value: min accepted value. Will cause ValidationError
           exception when value less than `min_value` passed during
           validation
        """
        super(IntField, self).__init__(details, **kwargs)

        self.max_value = max_value
        self.min_value = min_value

        if max_value is not None:
            self.validators.append(max_validator(max_value))
        if min_value is not None:
            self.validators.append(min_validator(min_value))

    def to_representation(self, value):
        return int(value)

    def from_representation(self, data):
        return int(data)


class FloatField(BaseField):
    type = 'float'

    def __init__(
            self,
            details,
            max_value=None,
            min_value=None,
            **kwargs
    ):
        """
        :param max_value: max accepted value. Will cause ValidationError
           exception when value greater than `max_value` passed during
           validation
        :param min_value: min accepted value. Will cause ValidationError
           exception when value less than `min_value` passed during
           validation
        """
        super(FloatField, self).__init__(details, **kwargs)

        self.max_value = max_value
        self.min_value = min_value

        if max_value is not None:
            self.validators.append(max_validator(max_value))
        if min_value is not None:
            self.validators.append(min_validator(min_value))

    def to_representation(self, value):
        return float(value)

    def from_representation(self, data):
        return float(data)
