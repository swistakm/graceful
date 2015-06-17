# -*- coding: utf-8 -*-
import falcon

from graceful.serializers import BaseSerializer
from graceful.fields import IntField, RawField
from graceful.parameters import StringParam
from graceful.validators import ValidationError
from graceful.resources.generic import (
    RetrieveUpdateDeleteAPI,
    PaginatedListCreateAPI,
)

api = application = falcon.API()

# lets pretend that this is our backend storage
CATS_STORAGE = [
    {"id": 0, "name": "kitty", "breed": "saimese"},
    {"id": 1, "name": "lucie", "breed": "maine coon"},
    {"id": 2, "name": "molly", "breed": "sphynx"},
]


def new_id():
    return max(map(lambda cat: cat['id'], CATS_STORAGE)) + 1


def is_lower_case(value):
    if value.lower() != value:
        raise ValidationError("{} is not lowercase".format(value))


# this is how we represent cats in our API
class CatSerializer(BaseSerializer):
    id = IntField("cat identification number", read_only=True)
    name = RawField("cat name", validators=[is_lower_case])
    breed = RawField("official breed name")


class V1(object):
    class Cat(RetrieveUpdateDeleteAPI):
        """
        Single cat identified by its id
        """
        serializer = CatSerializer()

        def get_cat(self, cat_id):
            try:
                return [cat for cat in CATS_STORAGE if cat['id'] == int(cat_id)][0]
            except IndexError:
                raise falcon.HTTPNotFound

        def update(self, params, meta, validated, **kwargs):
            cat_id = kwargs['cat_id']
            cat = self.get_cat(cat_id=cat_id)
            cat.update(validated)

            return validated

        def retrieve(self, params, meta, **kwargs):
            cat_id = kwargs['cat_id']
            return self.get_cat(cat_id)

        def delete(self, params, meta, **kwargs):
            cat_id = kwargs['cat_id']
            cat = self.get_cat(cat_id=cat_id)
            CATS_STORAGE.remove(cat)

    class CatList(PaginatedListCreateAPI):
        """
        List of all cats in our API
        """
        serializer = CatSerializer()

        breed = StringParam("set this param to filter cats by breed")

        def list(self, params, meta, **kwargs):
            if 'breed' in params:
                filtered = [
                    cat for cat in CATS_STORAGE if cat['breed'] == params['breed']
                ]
                return filtered
            else:
                return CATS_STORAGE

        def create(self, params, meta, validated, **kwargs):
            validated['id'] = new_id()
            CATS_STORAGE.append(validated)
            return validated

api.add_route("/v1/cats/{cat_id}", V1.Cat())
api.add_route("/v1/cats/", V1.CatList())
