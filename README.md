[![Build Status](https://travis-ci.org/swistakm/graceful.svg?branch=master)](https://travis-ci.org/swistakm/graceful)
[![Coverage Status](https://coveralls.io/repos/swistakm/graceful/badge.svg?branch=master)](https://coveralls.io/r/swistakm/graceful?branch=master)
[![Documentation Status](https://readthedocs.org/projects/graceful/badge/?version=latest)](https://graceful.readthedocs.io/en/latest/)
[![Join the chat at https://gitter.im/graceful-for-falcon/Lobby](https://badges.gitter.im/graceful-for-falcon/Lobby.svg)](https://gitter.im/graceful-for-falcon/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

# graceful

`graceful` is an elegant Python REST toolkit built on top of
[falcon](http://github.com/falconry/falcon) framework. It is highly inspired
by [Django REST framework](http://www.django-rest-framework.org/) - mostly by
how object serialization is done but more emphasis here is put on API to
be self-descriptive.

Features:

* generic classes for list and single object resources
* simple but extendable pagination
* simple but extendable authentication and authorization
* structured responses with content/meta separation
* declarative fields and parameters
* self-descriptive-everything: API description accessible both in python and
  through `OPTIONS` requests
* painless validation
* 100% tests coverage
* falcon>=0.3.0 (tested up to 1.1.x)
* python3 exclusive (tested from 3.3 to 3.6)

Community behind graceful is starting to grow but we don't have any mailing
list yet. There was one on [Librelist](http://librelist.com/browser/graceful)
but no one used it and it seems that librelist became dead (see GitHub
issue [#36](https://github.com/swistakm/graceful/issues/36)). For now let's use
gitter chat until we decide on something new.
Chat is available [here](https://gitter.im/graceful-for-falcon/Lobby).


## python3 only

**Important**: `graceful` is python3 exclusive because **right now** should be
a good time to forget about python2. There are no plans for making `graceful` 
python2 compatible although it would be pretty straightforward to do so with
existing tools (like six).

## usage
For extended tutorial and more information please refer to
[guide](https://graceful.readthedocs.org/en/latest/guide/) included in
documentation. 

Anyway here is simple example of working API made made with `graceful`:

```python
import falcon

from graceful.serializers import BaseSerializer
from graceful.fields import IntField, RawField
from graceful.parameters import StringParam
from graceful.resources.generic import (
    RetrieveAPI,
    PaginatedListAPI,
)

api = application = falcon.API()

# lets pretend that this is our backend storage
CATS_STORAGE = [
    {"id": 0, "name": "kitty", "breed": "saimese"},
    {"id": 1, "name": "lucie", "breed": "maine coon"},
    {"id": 2, "name": "molly", "breed": "sphynx"},
]


# this is how we represent cats in our API
class CatSerializer(BaseSerializer):
    id = IntField("cat identification number", read_only=True)
    name = RawField("cat name")
    breed = RawField("official breed name")


class Cat(RetrieveAPI):
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


    def retrieve(self, params, meta, **kwargs):
        cat_id = kwargs['cat_id']
        return self.get_cat(cat_id)

class CatList(PaginatedListAPI):
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

api.add_route("/v1/cats/{cat_id}", Cat())
api.add_route("/v1/cats/", CatList())
```

Assume this code is in python module named `example.py`.
Now run it with [gunicorn](https://github.com/benoitc/gunicorn):

    gunicorn -b localhost:8888 example

And you're ready to query it (here with awesome [httpie](http://httpie.org)
tool):

```
$ http localhost:8888/v0/cats/?breed=saimese
HTTP/1.1 200 OK
Connection: close
Date: Tue, 16 Jun 2015 08:43:05 GMT
Server: gunicorn/19.3.0
content-length: 116
content-type: application/json

{
    "content": [
        {
            "breed": "saimese",
            "id": 0,
            "name": "kitty"
        }
    ],
    "meta": {
        "params": {
            "breed": "saimese",
            "indent": 0
        }
    }
}
```

Or access API description issuing `OPTIONS` request:

```
$ http OPTIONS localhost:8888/v0/cats
HTTP/1.1 200 OK
Connection: close
Date: Tue, 16 Jun 2015 08:40:00 GMT
Server: gunicorn/19.3.0
allow: GET, OPTIONS
content-length: 740
content-type: application/json

{
    "details": "List of all cats in our API",
    "fields": {
        "breed": {
            "details": "official breed name",
            "label": null,
            "spec": null,
            "type": "string"
        },
        "id": {
            "details": "cat identification number",
            "label": null,
            "spec": null,
            "type": "int"
        },
        "name": {
            "details": "cat name",
            "label": null,
            "spec": null,
            "type": "string"
        }
    },
    "methods": [
        "GET",
        "OPTIONS"
    ],
    "name": "CatList",
    "params": {
        "breed": {
            "default": null,
            "details": "set this param to filter cats by breed",
            "label": null,
            "required": false,
            "spec": null,
            "type": "string"
        },
        "indent": {
            "default": "0",
            "details": "JSON output indentation. Set to 0 if output should not be formated.",
            "label": null,
            "required": false,
            "spec": null,
            "type": "integer"
        }
    },
    "path": "/v0/cats",
    "type": "list"
}
```


## contributing

Any contribution is welcome. Issues, suggestions, pull requests - whatever. 
There is only short set of rules that guide this project development you
should be aware of before submitting a pull request:

* Only requests that have passing CI builds (Travis) will be merged.
* Code is checked with `flakes8` and `pydocstyle` during build so this
  implicitly means that compliance with PEP-8 and PEP-257 is mandatory.
* No changes that decrease coverage will be merged.

One thing: if you submit a PR please do not rebase it later unless you
are asked for that explicitly. Reviewing pull requests that suddenly had
their history rewritten just drives me crazy.


## license

See `LICENSE` file.
