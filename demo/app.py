# -*- coding: utf-8 -*-
import falcon

from graceful.resources.generic import ObjectAPIResource, ListAPIResource
from graceful.serializers import BaseSerializer
from graceful.fields import IntField, RawField
from graceful.parameters import StringParam

api = application = falcon.API()

# lets pretend that this is our backend storage
CATS_STORAGE = [
    {"id": 0, "name": "kitty", "breed": "saimese"},
    {"id": 1, "name": "lucie", "breed": "maine coon"},
    {"id": 2, "name": "molly", "breed": "sphynx"},
]


# this is how we represent cats in our API
class CatSerializer(BaseSerializer):
    id = IntField("cat identification number")
    name = RawField("cat name")
    breed = RawField("official breed name")


# single cat resource
class Cat(ObjectAPIResource):
    """
    Single cat identified by its id
    """
    serializer = CatSerializer()

    def get_object(self, params, meta, cat_id, **kwargs):
        try:
            return [cat for cat in CATS_STORAGE if cat['id'] == int(cat_id)][0]
        except IndexError:
            raise falcon.HTTPNotFound


# cat list resource
class CatList(ListAPIResource):
    """
    List of all cats in our API
    """
    serializer = CatSerializer()

    breed = StringParam("set this param to filter cats by breed")

    def get_list(self, params, meta, **kwargs):
        if 'breed' in params:
            filtered = [
                cat for cat in CATS_STORAGE if cat['breed'] == params['breed']
            ]
            return filtered
        else:
            return CATS_STORAGE


api = application = falcon.API()
api.add_route("/v0/cats/", CatList())
api.add_route("/v0/cats/{cat_id}", Cat())
