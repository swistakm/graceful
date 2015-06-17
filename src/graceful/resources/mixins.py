# -*- coding: utf-8 -*-
import falcon
from graceful.parameters import IntParam
from graceful.resources.base import BaseAPIResource


class BaseMixin():
    def handle(self, handler, req, resp, **kwargs):
        params = self.require_params(req)

        meta, content = self.require_meta_and_content(
            handler, params, **kwargs
        )
        self.make_body(resp, params, meta, content)
        return content


class RetrieveMixin(BaseMixin):
    def retrieve(self, params, meta, **kwargs):
        raise NotImplementedError("retrieve method not implemented")

    def on_get(self, req, resp, handler=None, **kwargs):
        self.handle(
            handler or self.retrieve, req, resp, **kwargs
        )


class ListMixin(BaseMixin):
    def list(self, params, meta, **kwargs):
        raise NotImplementedError("list method not implemented")

    def on_get(self, req, resp, handler=None, **kwargs):
        self.handle(
            handler or self.list, req, resp, **kwargs
        )


class DeleteMixin(BaseMixin):
    def delete(self, params, meta, **kwargs):
        raise NotImplementedError("delete method not implemented")

    def on_delete(self, req, resp, handler=None, **kwargs):
        self.handle(
            handler or self.delete, req, resp, **kwargs
        )

        resp.status = falcon.HTTP_ACCEPTED


class UpdateMixin(BaseMixin):
    def update(self, params, meta, **kwargs):
        raise NotImplementedError("update method not implemented")

    def on_put(self, req, resp, handler=None, **kwargs):
        self.handle(
            handler or self.update, req, resp, **kwargs
        )
        resp.status = falcon.HTTP_ACCEPTED


class CreateMixin(BaseMixin):
    def create(self, params, meta, **kwargs):
        raise NotImplementedError("create method not implemented")

    def get_object_location(self, obj):
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


class PaginatedMixin(BaseAPIResource):
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
