from functools import partial

from graceful.resources.base import BaseResource
from graceful.resources.mixins import (
    RetrieveMixin,
    ListMixin,
    UpdateMixin,
    CreateMixin,
    DeleteMixin,
    PaginatedMixin,
    CreateBulkMixin
)


class Resource(RetrieveMixin, BaseResource):
    """Basic retrieval of resource instance lists without serialization.

    This resource class is intended for endpoints that do not require automatic
    representation serialization and extensive field descriptions but still
    gives support for defining parameters as resource class attributes.

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
    """Basic retrieval of resource instance lists without serialization.

    This resource class is intended for endpoints that do not require automatic
    representation serialization and extensive field descriptions but still
    gives support for defining parameters as resource class attributes.

    Example usage:

    .. code-block:

        from graceful.resources.generic import ListResource
        from graceful.parameters import StringParam

        class SampleResource(ListResource):
            some_filter = StringParam("some example filter parameter")

            def list(self, params, meta):
                return [{"sample": "resource"}]

    """


class RetrieveAPI(RetrieveMixin, BaseResource):
    """Generic Retrieve API with resource serialization.

    Generic resource that uses serializer for resource description,
    serialization and validation.

    Allowed methods:

    * GET: retrieve resource representation (handled with ``.retrieve()``
      method handler)

    """

    serializer = None

    def describe(self, req=None, resp=None, **kwargs):
        """Extend default endpoint description with serializer description."""
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
        """Respond on GET requests using ``self.retrieve()`` handler."""
        return super().on_get(
            req, resp, handler=self._retrieve, **kwargs
        )


class RetrieveUpdateAPI(UpdateMixin, RetrieveAPI):
    """Generic Retrieve/Update API with resource serialization.

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
        """Respond on PUT requests using ``self.update()`` handler."""
        validated = self.require_validated(req)
        return super().on_put(
            req, resp,
            handler=partial(self._update, validated=validated),
            **kwargs
        )


class RetrieveUpdateDeleteAPI(DeleteMixin, RetrieveUpdateAPI):
    """Generic Retrieve/Update/Delete API with resource serialization.

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
    """Generic List API with resource serialization.

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

    def describe(self, req=None, resp=None, **kwargs):
        """Extend default endpoint description with serializer description."""
        return super().describe(
            req, resp,
            type='list',
            fields=self.serializer.describe() if self.serializer else None,
            **kwargs
        )

    def on_get(self, req, resp, **kwargs):
        """Respond on GET requests using ``self.list()`` handler."""
        return super().on_get(req, resp, handler=self._list, **kwargs)


class ListCreateAPI(CreateMixin, CreateBulkMixin, ListAPI):
    """Generic List/Create API with resource serialization.

    Generic resource that uses serializer for resource description,
    serialization and validation.

    Allowed methods:

    * GET: list multiple resource instances representations (handled
      with ``.list()`` method handler)
    * POST: create new resource from representation provided in request body
      (handled with ``.create()`` method handler)
    * PATCH: create multiple resources from list of representations provided
      in request body (handled with ``.create_bulk()`` method handler.

    """

    def _create(self, params, meta, **kwargs):
        return self.serializer.to_representation(
            self.create(params, meta, **kwargs)
        )

    def _create_bulk(self, params, meta, **kwargs):
        return [
            self.serializer.to_representation(obj)
            for obj in self.create_bulk(params, meta, **kwargs)
        ]

    def create_bulk(self, params, meta, **kwargs):
        """Create items in bulk by reusing existing ``.create()`` handler.

        .. note::
            This is default create_bulk implementation that may not be safe
            to use in production environment depending on your implementation
            of ``.create()`` method handler.
        """
        validated = kwargs.pop('validated')
        return [
            self.create(params, meta, validated=item)
            for item in validated
        ]

    def on_post(self, req, resp, **kwargs):
        """Respond on POST requests using ``self.create()`` handler."""
        validated = self.require_validated(req)

        return super().on_post(
            req, resp,
            handler=partial(self._create, validated=validated),
            **kwargs
        )

    def on_patch(self, req, resp, **kwargs):
        """Respond on PATCH requests using ``self.create_bulk()`` handler."""
        validated = self.require_validated(req, bulk=True)

        return super().on_patch(
            req, resp,
            handler=partial(self._create_bulk, validated=validated),
            **kwargs
        )


class PaginatedListAPI(PaginatedMixin, ListAPI):
    """Generic List API with resource serialization and pagination.

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
    """Generic List/Create API with resource serialization and pagination.

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
