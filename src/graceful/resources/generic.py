# -*- coding: utf-8 -*-
from functools import partial

from graceful.parameters import IntParam
from graceful.resources.base import BaseAPIResource
from graceful.resources.mixins import (
    RetrieveMixin,
    ListMixin,
    UpdateMixin,
    CreateMixin,
    DeleteMixin,
    PaginatedMixin,
)


class ObjectAPIResource(BaseAPIResource):
    serializer = None

    def get_meta_and_content(self, req, params, **kwargs):
        meta, __ = super(ObjectAPIResource, self).get_meta_and_content(
            req, params
        )
        meta['type'] = 'list'

        content = self.serializer.to_representation(
            self.get_object(params, meta, **kwargs)
        )

        return meta, content

    def describe(self, req, resp, **kwargs):
        return super(ObjectAPIResource, self).describe(
            req, resp, type='object', **kwargs
        )

    def get_object(self, params, meta, **kwargs):
        raise NotImplementedError("get_object method not implemented")


class ListAPIResource(BaseAPIResource):
    serializer = None

    def get_meta_and_content(self, req, params, **kwargs):
        meta, __ = super(ListAPIResource, self).get_meta_and_content(
            req, params
        )

        content = [
            self.serializer.to_representation(obj)
            for obj in self.get_list(params, meta, **kwargs)
        ]

        return meta, content

    def describe(self, req, resp, **kwargs):
        return super(ListAPIResource, self).describe(
            req, resp, type='list', **kwargs
        )

    def get_list(self, params, meta, **kwargs):
        raise NotImplementedError("get_list method not implemented")


class PaginatedListAPIResource(ListAPIResource):
    """
    Basic paginated resource class. Adds two parameters to control basic
    (page size, page number) parameters with some default values.

    New `meta` dictionary entries included by this class:

    * `page_size`: response page size
    * `page`: response page number
    * `next`: query string that points to next page
    * `prev`: query string that point to previous page

    Defaults and description of pagination parameters can be simply overloaded
    by using new resource parameters e.g:

    class ThingsList(PaginatedListResource):
        page = IntParam(
            details="by default returns last item list",
            default="-1",
        )

    Note: `next` meta field will be always defined even if this query string
       can not yield any results unless additional `meta['has_more']`
       dict key is set to False. The best place to handle this is
       `resource.get_list(params, meta, **kwargs)` because this is obviously
       the only place where such information will be available.

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

    def get_meta_and_content(self, req, params, **kwargs):
        meta, content = super(
            PaginatedListAPIResource, self
        ).get_meta_and_content(req, params)

        self.add_pagination_meta(params, meta)
        return meta, content

    def add_pagination_meta(self, params, meta):
        meta['page_size'] = params['page_size']
        meta['page'] = params['page']

        meta['prev'] = "page={0}&page_size={1}".format(
            params['page'] - 1, params['page_size']
        ) if meta['page'] > 0 else None

        meta['next'] = "page={0}&page_size={1}".format(
            params['page'] + 1, params['page_size']
        ) if meta.get('has_more', True) else None


class RetrieveAPI(RetrieveMixin, BaseAPIResource):
    serializer = None

    def _retrieve(self, params, meta, **kwargs):
        return self.serializer.to_representation(
            self.retrieve(params, meta, **kwargs)
        )

    def on_get(self, req, resp, **kwargs):
        return super(RetrieveAPI, self).on_get(
            req, resp, handler=self._retrieve, **kwargs
        )


class RetrieveUpdateAPI(UpdateMixin, RetrieveAPI):
    def _update(self, params, meta, **kwargs):
        return self.serializer.to_representation(
            self.retrieve(params, meta, **kwargs)
        )

    def on_put(self, req, resp, **kwargs):
        validated = self.validated_object(req)

        return super(RetrieveUpdateAPI, self).on_put(
            req, resp,
            handler=partial(self._update, validated=validated),
            **kwargs
        )


class RetrieveUpdateDeleteAPI(DeleteMixin, RetrieveUpdateAPI):
    pass


class ListAPI(ListMixin, BaseAPIResource):
    def _list(self, params, meta, **kwargs):
        return [
            self.serializer.to_representation(obj)
            for obj in self.list(params, meta, **kwargs)
        ]

    def on_get(self, req, resp, **kwargs):
        return super(ListAPI, self).on_get(req, resp, handler=self._list)


class ListCreateAPI(CreateMixin, ListAPI):
    def _create(self, params, meta, **kwargs):
        return self.serializer.to_representation(
            self.create(params, meta, **kwargs)
        )

    def on_post(self, req, resp, **kwargs):
        validated = self.validated_object(req)

        return super(ListCreateAPI, self).on_post(
            req, resp,
            handler=partial(self._create, validated=validated),
            **kwargs
        )


class PaginatedListAPI(PaginatedMixin, ListAPI):
    def _list(self, params, meta, **kwargs):
        self.add_pagination_meta(params, meta)

        return super(PaginatedListAPI, self)._list(params, meta, **kwargs)


class PaginatedListCreateAPI(PaginatedMixin, ListCreateAPI):
    def _list(self, params, meta, **kwargs):
        self.add_pagination_meta(params, meta)

        return super(PaginatedListCreateAPI, self)._list(
            params, meta, **kwargs
        )

