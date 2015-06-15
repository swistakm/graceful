# -*- coding: utf-8 -*-
import urllib.parse
import base64
import decimal
import binascii
import inspect


class BaseParam():
    spec = None
    type = None

    def __init__(
            self,
            details,
            label=None,
            required=False,
            default=None,
    ):
        """
        Base parameter class for subclassing. To create new parameter type
        subclass `BaseField` and implement following methods:

        To create new field type subclass `BaseParam` and implement following
        methods:

        * `value()`

        Example:

            class BoolParam(BaseParam):
                def value(self, data):
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

        :param details: detailed description of parameter (it will be used for
            describing resource on OPTIONS requests).
        :param label: human readable label for this parameter (it will be used
            for describing resource on OPTIONS requests).
             Note: it is recommended to use parameter names that are
            self-explanatory intead of relying on param labels.
        :param required: if this parameter is required. If set to true
            then requests without parameter will raise BadRequest exception
        :param default: default value when this parameter is not specified.
            note: this needs to be a raw value since it will be also used to
            describe API resource.
        :return:
        """
        self.label = label
        self.details = details
        self.required = required

        if not (default is None) and not isinstance(default, str):
            raise TypeError(
                "value for {cls} 'default' argument must be string instance"
                "".format(cls=self.__class__.__name__)
            )

        if not (default is None) and required:
            raise ValueError(
                "{cls}(required={required}, default='{default}'): "
                "initialization with both required and default makes no sense"
                "".format(
                    cls=self.__class__.__name__,
                    default=default,
                    required=required,
                )
            )
        self.default = default

    def value(self, raw_value):
        raise NotImplementedError(
            "{cls}.value() method not implemented".format(
                cls=self.__class__.__name__
            )
        )

    def describe(self, **kwargs):
        description = {
            'label': self.label,
            # note: details are expected to be large so it should
            #       be reformatted
            'details': inspect.cleandoc(self.details),
            'required': self.required,
            'spec': self.spec,
            'default': self.default,
            'type': self.type or 'unspecified'
        }

        description.update(kwargs)
        return description


class StringParam(BaseParam):
    type = 'string'

    def value(self, raw_value):
        """Returns value as-is"""
        return raw_value


class UrlEncodedParam(BaseParam):
    type = 'percent-encoded string'
    spec = (
        "RFC-3968 Section 2.1",
        "https://tools.ietf.org/html/rfc3986#section-2.1",
    )

    def value(self, raw_value):
        """Decodes url encoded param"""
        return urllib.parse.unquote(raw_value)


class Base64EncodedParam(BaseParam):
    spec = (
        "RFC-4648 Section 4",
        "https://tools.ietf.org/html/rfc4648#section-4",
    )

    def value(self, raw_value):
        """Decodes param with Base64"""
        try:
            return base64.b64decode(bytes(raw_value, 'utf-8')).decode('utf-8')
        except binascii.Error as err:
            raise ValueError(str(err))


class IntParam(BaseParam):
    type = "integer"

    def value(self, raw_value):
        """Decodes param as integer value"""
        return int(raw_value)


class FloatParam(BaseParam):
    type = "float"

    def value(self, raw_value):
        """Decodes param as float value"""
        return float(raw_value)


class DecimalParam(BaseParam):
    type = "decimal"

    def value(self, raw_value):
        """Decodes param as decimal value"""
        try:
            return decimal.Decimal(raw_value)
        except decimal.InvalidOperation:
            raise ValueError(
                "Could not parse '{}' value as decimal".format(raw_value)
            )
