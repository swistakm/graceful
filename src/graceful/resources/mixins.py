from functools import partial

import falcon
from graceful.parameters import IntParam
from graceful.resources.base import BaseResource


class BaseMixin:
    """Base mixin class."""

    def handle(self, handler, req, resp, **kwargs):
        """Handle given resource manipulation flow in consistent manner.

        This mixin is intended to be used only as a base class in new flow
        mixin classes. It ensures that regardless of resource manunipulation
        semantics (retrieve, get, delete etc.) the flow is always the same:

        1. Decode and validate all request parameters from the query string
           using ``self.require_params()`` method.
        2. Use ``self.require_meta_and_content()`` method to construct ``meta``
           and ``content`` dictionaries that will be later used to create
           serialized response body.
        3. Construct serialized response body using ``self.body()`` method.

        Args:
             handler (method): resource manipulation method handler.
             req (falcon.Request): request object instance.
             resp (falcon.Response): response object instance to be modified.
             **kwargs: additional keyword arguments retrieved from url
                 template.

        Returns:
             Content dictionary (preferably resource representation).
        """
        params = self.require_params(req)

        # future: remove in 1.x
        if getattr(self, '_with_context', False):
            handler = partial(handler, context=req.context)

        meta, content = self.require_meta_and_content(
            handler, params, **kwargs
        )
        self.make_body(resp, params, meta, content)
        return content


class RetrieveMixin(BaseMixin):
    """Add default "retrieve flow on GET" to any resource class."""

    def retrieve(self, params, meta, **kwargs):
        """Retrieve existing resource instance and return its representation.

        Value returned by this handler will be included in response
        'content' section.

        Args:
            params (dict): dictionary of parsed parameters accordingly
                to definitions provided as resource class atributes.
            meta (dict): dictionary of meta parameters anything added
                to this dict will will be later included in response
                'meta' section. This can already prepopulated by method
                that calls this handler.
            **kwargs: dictionary of values retrieved from route url
                template by falcon. This is suggested way for providing
                resource identifiers.


        Returns:
            value to be included in response 'content' section

        """
        raise NotImplementedError("retrieve method not implemented")

    def on_get(self, req, resp, handler=None, **kwargs):
        """Respond on GET HTTP request assuming resource retrieval flow.

        This request handler assumes that GET requests are associated with
        single resource instance retrieval. Thus default flow for such requests
        is:

        * Retrieve single resource instance of prepare its representation by
          calling retrieve method handler.

        Args:
            req (falcon.Request): request object instance.
            resp (falcon.Response): response object instance to be modified
            handler (method): list method handler to be called. Defaults
                to ``self.list``.
            **kwargs: additional keyword arguments retrieved from url template.
        """
        self.handle(
            handler or self.retrieve, req, resp, **kwargs
        )


class ListMixin(BaseMixin):
    """Add default "list flow on GET" to any resource class."""

    def list(self, params, meta, **kwargs):
        """List existing resource instances and return their representations.

        Value returned by this handler will be included in response
        'content' section.

        Args:
            params (dict): dictionary of parsed parameters accordingly
               to definitions provided as resource class atributes.
            meta (dict): dictionary of meta parameters anything added
               to this dict will will be later included in response
               'meta' section. This can already prepopulated by method
               that calls this handler.
            **kwargs: dictionary of values retrieved from route url
               template by falcon. This is suggested way for providing
               resource identifiers.


        Returns:
            value to be included in response 'content' section

        """
        raise NotImplementedError("list method not implemented")

    def on_get(self, req, resp, handler=None, **kwargs):
        """Respond on GET HTTP request assuming resource list retrieval flow.

        This request handler assumes that GET requests are associated with
        resource list retrieval. Thus default flow for such requests is:

        * Retrieve list of existing resource instances and prepare their
          representations by calling list retrieval method handler.

        Args:
            req (falcon.Request): request object instance.
            resp (falcon.Response): response object instance to be modified
            handler (method): list method handler to be called. Defaults
                to ``self.list``.
            **kwargs: additional keyword arguments retrieved from url template.
        """
        self.handle(
            handler or self.list, req, resp, **kwargs
        )


class DeleteMixin(BaseMixin):
    """Add default "delete flow on DELETE" to any resource class."""

    def delete(self, params, meta, **kwargs):
        """Delete existing resource instance.

        Args:
            params (dict): dictionary of parsed parameters accordingly
               to definitions provided as resource class atributes.
            meta (dict): dictionary of meta parameters anything added
               to this dict will will be later included in response
               'meta' section. This can already prepopulated by method
               that calls this handler.
            **kwargs: dictionary of values retrieved from route url
               template by falcon. This is suggested way for providing
               resource identifiers.

        Returns:
            value to be included in response 'content' section

        """
        raise NotImplementedError("delete method not implemented")

    def on_delete(self, req, resp, handler=None, **kwargs):
        """Respond on DELETE HTTP request assuming resource deletion flow.

        This request handler assumes that DELETE requests are associated with
        resource deletion. Thus default flow for such requests is:

        * Delete existing resource instance.
        * Set response status code to ``202 Accepted``.

        Args:
            req (falcon.Request): request object instance.
            resp (falcon.Response): response object instance to be modified
            handler (method): deletion method handler to be called. Defaults
                to ``self.delete``.
            **kwargs: additional keyword arguments retrieved from url template.
        """
        self.handle(
            handler or self.delete, req, resp, **kwargs
        )

        resp.status = falcon.HTTP_ACCEPTED


class UpdateMixin(BaseMixin):
    """Add default "update flow on PUT" to any resource class."""

    def update(self, params, meta, **kwargs):
        """Update existing resource instance and return its representation.

        Value returned by this handler will be included in response
        'content' section.

        Args:
            params (dict): dictionary of parsed parameters accordingly
                to definitions provided as resource class atributes.
            meta (dict): dictionary of meta parameters anything added
                to this dict will will be later included in response
                'meta' section. This can already prepopulated by method
                that calls this handler.
            **kwargs: dictionary of values retrieved from route url
                template by falcon. This is suggested way for providing
                resource identifiers.

        Returns:
            value to be included in response 'content' section

        """
        raise NotImplementedError("update method not implemented")

    def on_put(self, req, resp, handler=None, **kwargs):
        """Respond on PUT HTTP request assuming resource update flow.

        This request handler assumes that PUT requests are associated with
        resource update/modification. Thus default flow for such requests is:

        * Modify existing resource instance and prepare its representation by
          calling its update method handler.
        * Set response status code to ``202 Accepted``.

        Args:
            req (falcon.Request): request object instance.
            resp (falcon.Response): response object instance to be modified
            handler (method): update method handler to be called. Defaults
                to ``self.update``.
            **kwargs: additional keyword arguments retrieved from url template.
        """
        self.handle(
            handler or self.update, req, resp, **kwargs
        )
        resp.status = falcon.HTTP_ACCEPTED


class CreateMixin(BaseMixin):
    """Add default "creation flow on POST" to any resource class."""

    def create(self, params, meta, **kwargs):
        """Create new resource instance and return its representation.

        This is default resource instance creation method. Value returned
        is the representation of single resource instance. It will be included
        in the 'content' section of response body.

        Args:
            params (dict): dictionary of parsed parameters accordingly
                to definitions provided as resource class atributes.
            meta (dict): dictionary of meta parameters anything added
                to this dict will will be later included in response
                'meta' section. This can already prepopulated by method
                that calls this handler.
            kwargs (dict): dictionary of values retrieved from route url
                template by falcon. This is suggested way for providing
                resource identifiers.


        Returns:
            value to be included in response 'content' section

        """
        raise NotImplementedError("create method not implemented")

    def get_object_location(self, obj):
        """Return location URI associated with given resource representation.

        This handler is optional. Returned URI will be included as the
        value of ``Location`` header on POST responses.
        """
        raise NotImplementedError("update method not implemented")

    def on_post(self, req, resp, handler=None, **kwargs):
        """Respond on POST HTTP request assuming resource creation flow.

        This request handler assumes that POST requests are associated with
        resource creation. Thus default flow for such requests is:

        * Create new resource instance and prepare its representation by
          calling its creation method handler.
        * Try to retrieve URI of newly created object using
          ``self.get_object_location()``. If it succeeds use that URI as the
          value of ``Location`` header in response object instance.
        * Set response status code to ``201 Created``.

        Args:
            req (falcon.Request): request object instance.
            resp (falcon.Response): response object instance to be modified
            handler (method): creation method handler to be called. Defaults
                to ``self.create``.
            **kwargs: additional keyword arguments retrieved from url template.
        """
        obj = self.handle(
            handler or self.create, req, resp, **kwargs
        )
        try:
            resp.location = self.get_object_location(obj)
        except NotImplementedError:
            pass

        resp.status = falcon.HTTP_CREATED


class CreateBulkMixin(BaseMixin):
    """Add default "bulk creation flow on PATCH" to any resource class."""

    def create_bulk(self, params, meta, **kwargs):
        """Create multiple resource instances and return their representation.

        This is default multiple resource instances creation method. Value
        returned is the representation of multiple resource instances. It will
        be included in the 'content' section of response body.

        Args:
            params (dict): dictionary of parsed parameters accordingly
                to definitions provided as resource class atributes.
            meta (dict): dictionary of meta parameters anything added
                to this dict will will be later included in response
                'meta' section. This can already prepopulated by method
                that calls this handler.
            kwargs (dict): dictionary of values retrieved from the route url
                template by falcon. This is suggested way for providing
                resource identifiers.

        Returns:
            value to be included in response 'content' section

        """
        raise NotImplementedError("create method not implemented")  # pragma: nocover # noqa

    def on_patch(self, req, resp, handler=None, **kwargs):
        """Respond on POST HTTP request assuming resource creation flow.

        This request handler assumes that POST requests are associated with
        resource creation. Thus default flow for such requests is:

        * Create new resource instances and prepare their representation by
          calling its bulk creation method handler.
        * Set response status code to ``201 Created``.

        **Note:** this handler does not set ``Location`` header by default as
        it would be valid only for single resource creation.

        Args:
            req (falcon.Request): request object instance.
            resp (falcon.Response): response object instance to be modified
            handler (method): creation method handler to be called. Defaults
                to ``self.create``.
            **kwargs: additional keyword arguments retrieved from url template.
        """
        self.handle(
            handler or self.create_bulk, req, resp, **kwargs
        )

        resp.status = falcon.HTTP_CREATED


class PaginatedMixin(BaseResource):
    """Add simple pagination capabilities to resource.

    This class provides two additional parameters with some default
    descriptions and ``add_pagination_meta`` method that can update
    meta with more useful pagination information.

    Example usage:

    .. code-block:: python

        from graceful.resources.mixins import PaginatedMixin
        from graceful.resources.generic import ListResource

        class SomeResource(PaginatedMixin, ListResource):

            def list(self, params, meta):
                # params has now 'page' and 'page_size' params that
                # can be used for offset&limit-like operations
                self.add_pagination_meta(params, meta)

                # ...

    """

    page_size = IntParam(
        details="""Specifies number of result entries in single response""",
        default='10'
    )
    page = IntParam(
        details="""Specifies number of results page for response.
        Page count starts from 0""",
        default='0',
    )

    def add_pagination_meta(self, params, meta):
        """Extend default meta dictionary value with pagination hints.

        Note:
            This method handler attaches values to ``meta`` dictionary without
            changing it's reference. This means that you should never replace
            ``meta`` dictionary with any other dict instance but simply modify
            its content.

        Args:
            params (dict): dictionary of decoded parameter values
            meta (dict): dictionary of meta values attached to response
        """
        meta['page_size'] = params['page_size']
        meta['page'] = params['page']

        meta['prev'] = "page={0}&page_size={1}".format(
            params['page'] - 1, params['page_size']
        ) if meta['page'] > 0 else None

        meta['next'] = "page={0}&page_size={1}".format(
            params['page'] + 1, params['page_size']
        ) if meta.get('has_more', True) else None
