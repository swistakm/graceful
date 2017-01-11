import json
import inspect
from collections import OrderedDict
from warnings import warn

from falcon import errors
import falcon
from mimeparse import parse_mime_type

from graceful.parameters import BaseParam, IntParam
from graceful.errors import DeserializationError, ValidationError


class MetaResource(type):
    """Metaclass for handling parametrization with parameter objects."""

    _params_storage_key = '_params'

    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        """Prepare class namespace in a way that ensures order of attributes.

        This needs to be an ``OrderedDict`` instance so ``_get_params()``
        method can construct params storage that preserves the same order of
        parameters as defined in code.

        Args:
            bases: all base classes of created resource class
            namespace (dict): namespace as dictionary of attributes

        """
        return OrderedDict()

    @classmethod
    def _get_params(mcs, bases, namespace):
        """Create params dictionary to be used in resource class namespace.

        Pop all parameter objects from attributes dict (namespace)
        and store them under _params_storage_key atrribute.
        Also collect all params from base classes in order that ensures
        params can be overriden.

        Args:
            bases: all base classes of created resource class
            namespace (dict): namespace as dictionary of attributes

        """
        params = [
            (name, namespace.pop(name))
            for name, attribute
            in list(namespace.items())
            if isinstance(attribute, BaseParam)
        ]

        for base in reversed(bases):
            if hasattr(base, mcs._params_storage_key):
                params = list(
                    getattr(base, mcs._params_storage_key).items()
                ) + params

        return OrderedDict(params)

    def __new__(mcs, name, bases, namespace, **kwargs):
        """Create new class object instance and alter its namespace."""
        namespace[mcs._params_storage_key] = mcs._get_params(bases, namespace)
        return super().__new__(
            # note: there is no need preserve order in namespace anymore so
            # we convert it explicitly to dict
            mcs, name, bases, dict(namespace),
        )

    def __init__(cls, name, bases, namespace, **kwargs):
        """Perform some additional class object initialization."""
        super().__init__(name, bases, namespace)

        try:
            # note: attribute is stored only if with_context keyword
            #       argument is not specified explicitly. This way
            #       we are able to guess if proper warning need to be
            #       displayed to the user.
            # future: remove in 1.x
            cls._with_context = kwargs.pop('with_context')
        except KeyError:
            pass


class BaseResource(metaclass=MetaResource):
    """Base resouce class with core param and response functionality.

    This base class handles resource responses, parameter deserialization,
    and validation of request included representations if serializer is
    defined.

    All custom resource classes based on ``BaseResource`` accept additional
    ``with_context`` keyword argument:


    .. code-block:: python

        class MyResource(BaseResource, with_context=True):
            ...

    The ``with_context`` argument tells if resource modification methods
    (metods injected with mixins - list/create/update/etc.) should accept
    the ``context`` argument in their signatures. For more details
    see :ref:`guide-context-aware-resources` section of documentation. The
    default value for ``with_context`` class keyword argument is ``False``.

    .. versionchanged:: 0.3.0
        Added the ``with_context`` keyword argument.

    """

    indent = IntParam(
        """
        JSON output indentation. Set to 0 if output should not be formated.
        """,
        default='0'
    )

    #: Instance of serializer class used to serialize/deserialize and
    #: validate resource representations.
    serializer = None

    def __new__(cls, *args, **kwargs):
        """Do some sanity checks before resource instance initialization."""
        instance = super().__new__(cls)

        if not hasattr(instance, '_with_context'):
            # note: warnings is displayed only if user did not specify
            #       explicitly that he want's his resource to not accept
            #       the context keyword argument.
            # future: remove in 1.x
            warn(
                """
                Class {} was defined without the 'with_context' keyword
                argument. This means that its resource manipulation
                methods (list/retrieve/create etc.) won't receive context
                keyword argument.

                This behaviour will change in 1.x version of graceful
                (please refer to documentation).
                """.format(cls),
                FutureWarning
            )
        return instance

    @property
    def params(self):
        """Return dictionary of parameter definition objects."""
        return getattr(self, self.__class__._params_storage_key)

    def make_body(self, resp, params, meta, content):
        """Construct response body in ``resp`` object using JSON serialization.

        Args:
            resp (falcon.Response): response object where to include
                serialized body
            params (dict): dictionary of parsed parameters
            meta (dict): dictionary of metadata to be included in 'meta'
                section of response
            content (dict): dictionary of response content (resource
                representation) to be included in 'content' section of response

        Returns:
            None

        """
        response = {
            'meta': meta,
            'content': content
        }
        resp.content_type = 'application/json'
        resp.body = json.dumps(
            response,
            indent=params['indent'] or None if 'indent' in params else None
        )

    def allowed_methods(self):
        """Return list of allowed HTTP methods on this resource.

        This is only for purpose of making resource description.

        Returns:
            list: list of allowed HTTP method names (uppercase)

        """
        return [
            method
            for method, allowed in (
                ('GET', hasattr(self, 'on_get')),
                ('POST', hasattr(self, 'on_post')),
                ('PUT', hasattr(self, 'on_put')),
                ('PATCH', hasattr(self, 'on_patch')),
                ('DELETE', hasattr(self, 'on_delete')),
                ('HEAD', hasattr(self, 'on_head')),
                ('OPTIONS', hasattr(self, 'on_options')),
            ) if allowed
        ]

    def describe(self, req=None, resp=None, **kwargs):
        """Describe API resource using resource introspection.

        Additional description on derrived resource class can be added using
        keyword arguments and calling ``super().decribe()`` method call
        like following:

        .. code-block:: python

             class SomeResource(BaseResource):
                 def describe(req, resp, **kwargs):
                     return super().describe(
                         req, resp, type='list', **kwargs
                      )

        Args:
            req (falcon.Request): request object
            resp (falcon.Response): response object
            kwargs (dict): dictionary of values created from resource url
                template

        Returns:
            dict: dictionary with resource descritpion information

        .. versionchanged:: 0.2.0
           The `req` and `resp` parameters became optional to ease the
           implementation of application-level documentation generators.
        """
        description = {
            'params': OrderedDict([
                (name, param.describe())
                for name, param in self.params.items()
            ]),
            'details':
                inspect.cleandoc(
                    self.__class__.__doc__ or
                    "This resource does not have description yet"
                ),
            'name': self.__class__.__name__,
            'methods': self.allowed_methods()
        }
        # note: add path to resource description only if request object was
        #       provided in order to make auto-documentation engines simpler
        if req:
            description['path'] = req.path

        description.update(**kwargs)
        return description

    def on_options(self, req, resp, **kwargs):
        """Respond with JSON formatted resource description on OPTIONS request.

        Args:
            req (falcon.Request): Optional request object. Defaults to None.
            resp (falcon.Response): Optional response object. Defaults to None.
            kwargs (dict): Dictionary of values created by falcon from
                resource uri template.

        Returns:
            None


        .. versionchanged:: 0.2.0
           Default ``OPTIONS`` responses include ``Allow`` header with list of
           allowed HTTP methods.
        """
        resp.set_header('Allow', ', '.join(self.allowed_methods()))
        resp.body = json.dumps(self.describe(req, resp))
        resp.content_type = 'application/json'

    def require_params(self, req):
        """Require all defined parameters from request query string.

        Raises ``falcon.errors.HTTPMissingParam`` exception if any of required
        parameters is missing and ``falcon.errors.HTTPInvalidParam`` if any
        of parameters could not be understood (wrong format).

        Args:
            req (falcon.Request): request object

        """
        params = {}

        for name, param in self.params.items():
            if name not in req.params and param.required:
                # we could simply raise with this single param or use get_param
                # with required=True parameter but for client convenience
                # we prefer to list all missing params that are required
                missing = set(
                    p for p in self.params
                    if self.params[p].required
                ) - set(req.params.keys())

                raise errors.HTTPMissingParam(", ".join(missing))

            elif name in req.params or param.default:
                # Note: lack of key in req.params means it was not specified
                # so unless there is default value it will not be included in
                # output params dict.
                # This way we have explicit information that param was
                # not specified. Using None would not be as good because param
                # class can also return None from `.value()` method as a valid
                # translated value.
                try:
                    if param.many:
                        # params with "many" enabled need special care
                        values = req.get_param_as_list(
                            # note: falcon allows to pass value handler using
                            #       `transform` param so we do not need to
                            #       iterate through list manually
                            name, param.validated_value
                        ) or [
                            param.default and
                            param.validated_value(param.default)
                        ]
                        params[name] = param.container(values)
                    else:
                        # note that if many==False and query parameter
                        # occurs multiple times in qs then it is
                        # **unspecified** which one will be used. See:
                        # http://falcon.readthedocs.org/en/latest/api/request_and_response.html#falcon.Request.get_param  # noqa
                        params[name] = param.validated_value(
                            req.get_param(name, default=param.default)
                        )

                except ValidationError as err:
                    # ValidationError allows to easily translate itself to
                    # to falcon's HTTPInvalidParam (Bad Request HTTP response)
                    raise err.as_invalid_param(name)

                except ValueError as err:
                    # Other parsing issues are expected to raise ValueError
                    raise errors.HTTPInvalidParam(str(err), name)

        return params

    def require_meta_and_content(self, content_handler, params, **kwargs):
        """Require 'meta' and 'content' dictionaries using proper hander.

        Args:
            content_handler (callable): function that accepts
                ``params, meta, **kwargs`` argument and returns dictionary
                for ``content`` response section
            params (dict): dictionary of parsed resource parameters
            kwargs (dict): dictionary of values created from resource url
                template

        Returns:
            tuple (meta, content): two-tuple with dictionaries of ``meta`` and
                ``content`` response sections

        """
        meta = {
            'params': params
        }
        content = content_handler(params, meta, **kwargs)
        meta['params'] = params
        return meta, content

    def require_representation(self, req):
        """Require raw representation dictionary from falcon request object.

        This does not perform any field parsing or validation but only uses
        allowed content-encoding handler to decode content body.

        Note:
            Currently only JSON is allowed as content type.

        Args:
            req (falcon.Request): request object

        Returns:
            dict: raw dictionary of representation supplied in request body

        """
        try:
            type_, subtype, _ = parse_mime_type(req.content_type)
            content_type = '/'.join((type_, subtype))
        except:
            raise falcon.HTTPUnsupportedMediaType(
                description="Invalid Content-Type header: {}".format(
                    req.content_type
                )
            )

        if content_type == 'application/json':
            body = req.stream.read()
            return json.loads(body.decode('utf-8'))
        else:
            raise falcon.HTTPUnsupportedMediaType(
                description="only JSON supported, got: {}".format(content_type)
            )

    def require_validated(self, req, partial=False, bulk=False):
        """Require fully validated internal object dictionary.

        Internal object dictionary creation is based on content-decoded
        representation retrieved from request body. Internal object validation
        is performed using resource serializer.

        Args:
            req (falcon.Request): request object
            partial (bool): set to True if partially complete representation
                is accepted (e.g. for patching instead of full update). Missing
                fields in representation will be skiped.
            bulk (bool): set to True if request payload represents multiple
                resources instead of single one.

        Returns:
            dict: dictionary of fields and values representing internal object.
                Each value is a result of ``field.from_representation`` call.

        """
        representations = [
            self.require_representation(req)
        ] if not bulk else self.require_representation(req)

        if bulk and not isinstance(representations, list):
            raise ValidationError(
                "Request payload should represent a list of resources."
            ).as_bad_request()

        object_dicts = []

        try:
            for representation in representations:
                object_dict = self.serializer.from_representation(
                    representation
                )
                self.serializer.validate(object_dict, partial)
                object_dicts.append(object_dict)

        except DeserializationError as err:
            # when working on Resource we know that we can finally raise
            # bad request exceptions
            raise err.as_bad_request()

        except ValidationError as err:
            # ValidationError is a suggested way to validate whole resource
            # so we also are prepared to catch it
            raise err.as_bad_request()

        return object_dicts if bulk else object_dicts[0]
