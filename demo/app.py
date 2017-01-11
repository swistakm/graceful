import falcon

from graceful.serializers import BaseSerializer
from graceful.fields import IntField, StringField
from graceful.parameters import StringParam
from graceful.errors import ValidationError
from graceful.resources.generic import (
    RetrieveUpdateDeleteAPI,
    PaginatedListCreateAPI,
)

from jinja2 import Environment, FileSystemLoader

# environment allows us to load template files, 'templates' is a dir
# where we want to store them
env = Environment(loader=FileSystemLoader('templates'))

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
    name = StringField("cat name", validators=[is_lower_case])
    breed = StringField("official breed name")


class V1():
    class Cat(RetrieveUpdateDeleteAPI):
        """
        Single cat identified by its id
        """
        serializer = CatSerializer()

        def get_cat(self, cat_id):
            try:
                return [
                    cat for cat in CATS_STORAGE if cat['id'] == int(cat_id)
                ][0]
            except IndexError:
                raise falcon.HTTPNotFound

        def update(self, params, meta, validated, **kwargs):
            cat_id = kwargs['cat_id']
            cat = self.get_cat(cat_id=cat_id)
            cat.update(validated)

            return validated

        def on_get(self, req, resp, **kwargs):
            super().on_get(req, resp, additional=None, **kwargs)

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
                    cat for cat in CATS_STORAGE
                    if cat['breed'] == params['breed']
                ]
                return filtered
            else:
                return CATS_STORAGE

        def create(self, params, meta, validated, **kwargs):
            validated['id'] = new_id()
            CATS_STORAGE.append(validated)
            return validated


class Templated(object):
    template_name = None

    def __init__(self, template_name=None, context=None):
        # note: this is to ensure that template_name can be set as
        #       class level attribute in derrived class
        self.template_name = template_name or self.template_name
        self.context = context or {}

    def render(self, req, resp):
        template = env.get_template(self.template_name)
        return template.render(**self.context)

    def on_get(self, req, resp):
        resp.body = self.render(req, resp)
        resp.content_type = 'text/html'

api = application = falcon.API()

endpoints = {
    "/v1/cats/{cat_id}": V1.Cat(),
    "/v1/cats/": V1.CatList(),
}

for uri, endpoint in endpoints.items():
    # add resource endpoints
    api.add_route(uri, endpoint)

# create documentation resource from API endpoints
# and add it to the router
api.add_route("/", Templated('index.html', {
    'endpoints': {
        uri: endpoint.describe()
        for uri, endpoint
        in endpoints.items()
    }
}))
