# -*- coding: utf-8 -*-
import falcon
from graceful.parameters import IntParam
from graceful.resources.base import BaseResource


class BaseMixin():
    """Base mixin class"""
    def handle(self, handler, req, resp, **kwargs):
        params = self.require_params(req)

        meta, content = self.require_meta_and_content(
            handler, params, **kwargs
        )
        self.make_body(resp, params, meta, content)
        return content


class RetrieveMixin(BaseMixin):
    """
    Add retrieve capabilities to resource with GET requests.
    """

    def retrieve(self, params, meta, **kwargs):
        """
        Retrieve object method handler

        Value returned by this handler will be included in response
        'content' section.

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
        raise NotImplementedError("retrieve method not implemented")

    def on_get(self, req, resp, handler=None, **kwargs):
        self.handle(
            handler or self.retrieve, req, resp, **kwargs
        )


class ListMixin(BaseMixin):
    """
    Add list capabilities to resource with GET requests.
    """

    def list(self, params, meta, **kwargs):
        """
        List objects method handler

        Value returned by this handler will be included in response
        'content' section.

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
        raise NotImplementedError("list method not implemented")

    def on_get(self, req, resp, handler=None, **kwargs):
        self.handle(
            handler or self.list, req, resp, **kwargs
        )


class DeleteMixin(BaseMixin):
    """
    Add delete capabilities to resource with DELETE requests.
    """

    def delete(self, params, meta, **kwargs):
        """
        Delete object method handler

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
        raise NotImplementedError("delete method not implemented")

    def on_delete(self, req, resp, handler=None, **kwargs):
        self.handle(
            handler or self.delete, req, resp, **kwargs
        )

        resp.status = falcon.HTTP_ACCEPTED


class UpdateMixin(BaseMixin):
    """
    Add update capabilities to resource with PUT requests.
    """

    def update(self, params, meta, **kwargs):
        """
        Update object method handler

        Value returned by this handler will be included in response
        'content' section.

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
        raise NotImplementedError("update method not implemented")

    def on_put(self, req, resp, handler=None, **kwargs):
        self.handle(
            handler or self.update, req, resp, **kwargs
        )
        resp.status = falcon.HTTP_ACCEPTED


class CreateMixin(BaseMixin):
    """
    Add create capabilities to resource with POST requests.
    """
    def create(self, params, meta, **kwargs):
        """
        Create object method handler

        Value returned by this handler will be included in response
        'content' section.

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
        """
        Return location path that will be included as Location header.

        This handler is optional.

        """
        raise NotImplementedError("update method not implemented")

    def on_post(self, req, resp, handler=None, **kwargs):
        obj = self.handle(
            handler or self.create, req, resp, **kwargs
        )
        try:
            resp.location = self.get_object_location(obj)
        except NotImplementedError:
            pass

        resp.status = falcon.HTTP_CREATED


class PaginatedMixin(BaseResource):
    """
    Add simple pagination capabilities to resource.

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
        meta['page_size'] = params['page_size']
        meta['page'] = params['page']

        meta['prev'] = "page={0}&page_size={1}".format(
            params['page'] - 1, params['page_size']
        ) if meta['page'] > 0 else None

        meta['next'] = "page={0}&page_size={1}".format(
            params['page'] + 1, params['page_size']
        ) if meta.get('has_more', True) else None
