# -*- coding: utf-8 -*-
import json
import inspect
from collections import OrderedDict

from falcon import errors
import falcon

from graceful.parameters import BaseParam, IntParam
from graceful.serializers import DeserializationError


class MetaResource(type):
    """ Metaclass for handling parametrization with parameter objects
    """
    _params_storage_key = '_params'

    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        """
        Prepare class namespace in a way that ensures order of attributes.
        This needs to be an `OrderedDict` so `_get_params()` method can
        construct params storage that preserves the same order of parameters
        as defined in code.

        Note: this is python3 thing and support for ordering of params in
        descriptions will not be backported to python2 even if this framework
        will get python2 support.
        """
        return OrderedDict()

    @classmethod
    def _get_params(mcs, bases, namespace):
        """ Pop all parameter objects from attributes dict (namespace)
        and store them under _params_storage_key atrribute.
        Also collect all params from base classes in order that ensures
        params can be overriden.

        :param bases: all base classes of created resource class
        :param namespace: namespace as dictionary of attributes
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

    def __new__(mcs, name, bases, namespace):
        namespace[mcs._params_storage_key] = mcs._get_params(bases, namespace)

        return super(MetaResource, mcs).__new__(
            # note: there is no need preserve order in namespace anymore so
            # we convert it explicitely to dict
            mcs, name, bases, dict(namespace)
        )


class BaseAPIResource(object, metaclass=MetaResource):
    indent = IntParam(
        """
        JSON output indentation. Set to 0 if output should not be formated.
        """,
        default='0'
    )

    serializer = None

    @property
    def params(self):
        return getattr(self, self.__class__._params_storage_key)

    def get_meta_and_content(self, req, params, **kwargs):
        """
        Return tuple of meta and content dictionaries.

        `meta` contains dictionary of additional information that describes
        current API request (parsed parameters, pagination, telemetry)

        `content` is an actual request result: representation of specific
        resource.

        :param req: request object
        :param params: dictionary of parsed parameters
        :param kwargs: dictionary of keyword arguments parsed from resource
            url template.
        :return: two-tuple containing (meta, content) dictionaries
        """
        return {
            'params': params
        }, {}

    def require_params(self, req):
        """
        Perform basic required parameters check.

        Raises falcon.errors.HTTPMissingParam if any of required prameters
        is missing
        """
        # TODO: handle specifying parameter multiple times in query string!
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
                    params[name] = param.value(
                        req.get_param(name, default=param.default)
                    )
                except ValueError as err:
                    raise errors.HTTPInvalidParam(str(err), name)

        return params

    def on_get(self, req, resp, **kwargs):
        """
        Respond with resource representation in as application/json content
        type
        """
        params = self.require_params(req)
        meta, content = self.get_meta_and_content(req, params, **kwargs)

        response = {
            'meta': meta,
            'content': content
        }

        resp.body = json.dumps(response, indent=params['indent'] or None)

        resp.content_type = 'application/json'

    def make_body(self, resp, meta, content):
        response = {
            'meta': meta,
            'content': content
        }
        resp.content_type = 'application/json'
        resp.body = json.dumps(response)

    def require_meta_and_content(self, content_handler, params, **kwargs):
        meta = {
            'params': params
        }
        content = content_handler(params, meta, **kwargs)
        meta['params'] = params
        return meta, content

    def allowed_methods(self):
        return [
            method
            for method, allowed in (
                ('GET', hasattr(self, 'on_get')),
                ('POST', hasattr(self, 'on_post')),
                ('PUT', hasattr(self, 'on_put')),
                ('DELETE', hasattr(self, 'on_delete')),
                ('HEAD', hasattr(self, 'on_head')),
                ('OPTIONS', hasattr(self, 'on_options')),
            ) if allowed
        ]

    def describe(self, req, resp, **kwargs):
        """
        Describe API resource using class introspection, self-describing
        serializer and current request object (for resource guessing path)

        Additional description on derrived resource class can be added using
        keyword arguments and calling super().decribe() method call
        like following:

             class SomeResource(BaseAPIResource):
                 def describe(req, resp, **kwargs):
                     return super(SomeResource, self).describe(
                         req, resp, type='list', **kwargs
                      )

        :param req: falcon.Request object
        :param resp: falcon.Response object
        :param kwargs: additional keyword arguments to extend resource
            description
        :return: dict with resource descritpion information
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
            'fields': self.serializer.describe() if self.serializer else None,
            'path': req.path,
            'name': self.__class__.__name__,
            'methods': self.allowed_methods()
        }
        description.update(**kwargs)
        return description

    def on_options(self, req, resp, **kwargs):
        """
        Respond with JSON formatted resource description.

        Note: accepting additional **kwargs is necessary to be able to respond
            to OPTIONS requests if resource is routed in falcon with url
            template

        :param req: falcon.Request object
        :param resp: falcon.Responce object
        :param kwargs: dict with additional arguments that can can be passed
            to OPTIONS (ignored)
        :return: None
        """
        resp.body = json.dumps(self.describe(req, resp))
        resp.content_type = 'application/json'

    def require_representation(self, req):
        if req.content_type == 'application/json':
            body = req.stream.read()
            return json.loads(body.decode('utf-8'))
        else:
            raise falcon.HTTPUnsupportedMediaType(
                description="only JSON supported"
            )

    def validated_object(self, req, partial=False):
        representation = self.require_representation(req)

        try:
            object_dict = self.serializer.from_representation(representation)
            self.serializer.validate(object_dict, partial)

        except DeserializationError as err:
            # when working on Resource we know that we can finally raise
            # bad request exceptions
            raise err.as_bad_request()

        return object_dict
