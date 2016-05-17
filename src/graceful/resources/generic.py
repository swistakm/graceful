# -*- coding: utf-8 -*-
from functools import partial

from graceful.resources.base import BaseResource
from graceful.resources.mixins import (
    RetrieveMixin,
    ListMixin,
    UpdateMixin,
    CreateMixin,
    DeleteMixin,
    PaginatedMixin,
)


class Resource(RetrieveMixin, BaseResource):
    """
    Generic resource for single object retrieve type of endpoints without use
    of automatic representation serialization and extensive field descriptions.

    This still gives support for defining parameters.

    Example usage:

    .. code-block:

        from graceful.resources.generic import Resource
        from graceful.parameters import StringParam

        class SampleResource(Resource):
            dummy = StringParam("some example dummy parameter")

            def retrieve(self, params, meta):
                return {"sample": "resource"}

    """


class ListResource(ListMixin, BaseResource):
    """
    Generic resource for list object type of endpoints without use of
    automatic representation serialization and extensive field descriptions

    This still gives support for defining parameters.

    Example usage:

    .. code-block:

        from graceful.resources.generic import ListResource
        from graceful.parameters import StringParam

        class SampleResource(ListResource):
            some_filter = StringParam("some example filter parameter")

            def list(self, params, meta):
                return [{"sample": "resource"}]

    """
    pass


class RetrieveAPI(RetrieveMixin, BaseResource):
    """
    Generic resource that uses serializer for resource description,
    serialization and validation.

    Allowed methods:

    * GET: retrieve resource representation (handled with ``.retrieve()``
      method handler)

    """
    serializer = None

    def describe(self, req, resp, **kwargs):
        return super().describe(
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
        return super().on_get(
            req, resp, handler=self._retrieve, **kwargs
        )


class RetrieveUpdateAPI(UpdateMixin, RetrieveAPI):
    """
    Generic resource that uses serializer for resource description,
    serialization and validation.

    Allowed methods:

    * GET: retrieve resource representation handled with ``.retrieve()``
      method handler
    * PUT: update resource with representation provided in request body
      (handled with ``.update()`` method handler)

    """
    def _update(self, params, meta, **kwargs):
        return self.serializer.to_representation(
            self.update(params, meta, **kwargs)
        )

    def on_put(self, req, resp, **kwargs):
        validated = self.require_validated(req)
        return super().on_put(
            req, resp,
            handler=partial(self._update, validated=validated),
            **kwargs
        )


class RetrieveUpdateDeleteAPI(DeleteMixin, RetrieveUpdateAPI):
    """
    Generic resource that uses serializer for resource description,
    serialization and validation.

    Allowed methods:

    * GET: retrieve resource representation (handled with ``.retrieve()``
      method handler)
    * PUT: update resource with representation provided in request body
      (handled with ``.update()`` method handler)
    * DELETE: delete resource (handled with ``.delete()`` method handler)

    """


class ListAPI(ListMixin, BaseResource):
    """
    Generic resource that uses serializer for resource description,
    serialization and validation.

    Allowed methods:

    * GET: list multiple resource instances representations (handled
      with ``.list()`` method handler)

    """
    def _list(self, params, meta, **kwargs):
        return [
            self.serializer.to_representation(obj)
            for obj in self.list(params, meta, **kwargs)
        ]

    def describe(self, req, resp, **kwargs):
        return super().describe(
            req, resp,
            type='list',
            fields=self.serializer.describe() if self.serializer else None,
            **kwargs
        )

    def on_get(self, req, resp, **kwargs):
        return super().on_get(req, resp, handler=self._list, **kwargs)


class ListCreateAPI(CreateMixin, ListAPI):
    """
    Generic resource that uses serializer for resource description,
    serialization and validation.

    Allowed methods:

    * GET: list multiple resource instances representations (handled
      with ``.list()`` method handler)
    * POST: create new resource from representation provided in request body
      (handled with ``.create()`` method handler)

    """
    def _create(self, params, meta, **kwargs):
        return self.serializer.to_representation(
            self.create(params, meta, **kwargs)
        )

    def on_post(self, req, resp, **kwargs):
        validated = self.require_validated(req)

        return super().on_post(
            req, resp,
            handler=partial(self._create, validated=validated),
            **kwargs
        )


class PaginatedListAPI(PaginatedMixin, ListAPI):
    """
    Generic resource that uses serializer for resource description,
    serialization and validation.

    Adds simple pagination to list of resources.

    Allowed methods:

    * GET: list multiple resource instances representations (handled
      with ``.list()`` method handler)

    """
    def _list(self, params, meta, **kwargs):
        objects = super()._list(params, meta, **kwargs)
        # note: we need to populate meta after objects are retrieved
        self.add_pagination_meta(params, meta)
        return objects


class PaginatedListCreateAPI(PaginatedMixin, ListCreateAPI):
    """
    Generic resource that uses serializer for resource description,
    serialization and validation.

    Adds simple pagination to list of resources.

    Allowed methods:

    * GET: list multiple resource instances representations (handled
      with ``.list()`` method handler)
    * POST: create new resource from representation provided in request body
      (handled with ``.create()`` method handler)

    """
    def _list(self, params, meta, **kwargs):
        objects = super()._list(
            params, meta, **kwargs
        )
        # note: we need to populate meta after objects are retrieved
        self.add_pagination_meta(params, meta)
        return objects
