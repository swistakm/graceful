# -*- coding: utf-8 -*-
import base64
import decimal
import binascii
import inspect


class BaseParam():
    """
    Base parameter class for subclassing. To create new parameter type
    subclass ``BaseField`` and implement following methods:

    To create new field type subclass ``BaseParam`` and implement ``.value()``
    method handlers.


    Args:

        details (str): verbose description of parameter. Should contain all
           information that may be important to your API user and will be used
           for describing resource on ``OPTIONS`` requests and ``.describe()``
           call.

        label (str): human readable label for this parameter (it will be used
           for describing resource on OPTIONS requests).

           *Note that it is recomended to use parameter names that are
           self-explanatory intead of relying on param labels.*

        required (bool): if set to ``True`` then all GET, POST, PUT,
           PATCH and DELETE requests will return ``400 Bad Request`` response
           if query param is not provided. Defaults to ``False``.

        default (str): set default value for param if it is not
           provided in request as query parameter. This MUST be a raw string
           value that will be then parsed by ``.value()`` handler.

           If default is set and ``required`` is ``True`` it will raise
           ``ValueError`` as having required parameters with default
           value has no sense.

        param (str): set to ``True`` if multiple occurences of this parameter
           can be included in query string, as a result values for this
           parameter will be always included as a list in params dict. Defaults
           to ``False``.

          .. note::
             If ``many=False`` and client inlcudes multiple values for this
             parameter in query string then only one of those values will be
             returned, and it is undefined which one.

    Example:

    .. code-block:: python

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

    """
    spec = None
    type = None

    def __init__(
            self,
            details,
            label=None,
            required=False,
            default=None,
            many=False,
    ):
        self.label = label
        self.details = details
        self.required = required
        self.many = many

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
        """
        Raw value deserializtion method handler

        Args:
            raw_value (str) - raw value from GET parameters

        """
        raise NotImplementedError(
            "{cls}.value() method not implemented".format(
                cls=self.__class__.__name__
            )
        )

    def describe(self, **kwargs):
        """
        Describe this parameter instance for purpose of self-documentation.

        Args:
            kwargs (dict): dictionary of additional description items for
               extending default description

        Returns:
            dict: dictionary of description items


        Suggested way for overriding description fields or extending it with
        additional items is calling super class method with new/overriden
        fields passed as keyword arguments like following:

        .. code-block:: python

            class DummyParam(BaseParam):
               def description(self, **kwargs):
                   super().describe(is_dummy=True, **kwargs)

        """

        description = {
            'label': self.label,
            # note: details are expected to be large so it should
            #       be reformatted
            'details': inspect.cleandoc(self.details),
            'required': self.required,
            'many': self.many,
            'spec': self.spec,
            'default': self.default,
            'type': self.type or 'unspecified'
        }

        description.update(kwargs)
        return description


class StringParam(BaseParam):
    """
    Describes parameter that will always be returned in same form as provided
    in query string. Still additional validation can be added to param instance
    e.g.:

    .. code-block:: python

        from graceful.parameters import StringParam
        from graceful.validators import match_validator
        from graceful.resources.generic import Resource

        class ExampleResource(Resource):
            word = StringParam(
                'one "word" parameter',
                validators=[match_validator('\w+')],
            )

    """
    type = 'string'

    def value(self, raw_value):
        """Returns value as-is (str)"""
        return raw_value


class Base64EncodedParam(BaseParam):
    """
    Describes string parameter that has value encoded using Base64 encoding
    """
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
    """
    Describes parameter that has value expressed as integer number
    """
    type = "integer"

    def value(self, raw_value):
        """Decodes param as integer value"""
        return int(raw_value)


class FloatParam(BaseParam):
    """
    Describes parameter that has value expressed as float number
    """
    type = "float"

    def value(self, raw_value):
        """Decodes param as float value"""
        return float(raw_value)


class DecimalParam(BaseParam):
    """
    Describes parameter that has value expressed as decimal number
    """
    type = "decimal"

    def value(self, raw_value):
        """Decodes param as decimal value"""
        try:
            return decimal.Decimal(raw_value)
        except decimal.InvalidOperation:
            raise ValueError(
                "Could not parse '{}' value as decimal".format(raw_value)
            )
