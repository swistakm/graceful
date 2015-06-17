# -*- coding: utf-8 -*-
from functools import partial

from graceful.resources.base import BaseAPIResource
from graceful.resources.mixins import (
    RetrieveMixin,
    ListMixin,
    UpdateMixin,
    CreateMixin,
    DeleteMixin,
    PaginatedMixin,
)


class Resource(RetrieveMixin, BaseAPIResource):
    pass


class RetrieveAPI(RetrieveMixin, BaseAPIResource):
    serializer = None

    def describe(self, req, resp, **kwargs):
        return super(RetrieveAPI, self).describe(
            req, resp,
            type='object',
            fields=self.serializer.describe() if self.serializer else None,
            **kwargs
        )

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
            self.update(params, meta, **kwargs)
        )

    def on_put(self, req, resp, **kwargs):
        validated = self.require_validated(req)
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

    def describe(self, req, resp, **kwargs):
        return super(ListAPI, self).describe(
            req, resp,
            type='list',
            fields=self.serializer.describe() if self.serializer else None,
            **kwargs
        )

    def on_get(self, req, resp, **kwargs):
        return super(ListAPI, self).on_get(req, resp, handler=self._list)


class ListCreateAPI(CreateMixin, ListAPI):
    def _create(self, params, meta, **kwargs):
        return self.serializer.to_representation(
            self.create(params, meta, **kwargs)
        )

    def on_post(self, req, resp, **kwargs):
        validated = self.require_validated(req)

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
