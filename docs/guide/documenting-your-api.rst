Documenting your API
--------------------

Providing clear and readable documentation is very important topic for every
API creator. Graceful does not come with built-in autodoc feature yet, but
is built in a way that allows you to create your documentation very easily.

Every important building block that creates your API definition in graceful
(resource, parameter, and field classes) comes with special ``describe()``
method that returns dictionary of all important metadata necessary to create
clear and readable documentation. Additionally generic API resources
(:any:`RetrieveAPI`, :any:`ListAPI`, :any:`ListCreateAPI` and so on) are aware
of their associated serializers to ease the whole process of documenting your
service.


Using self-descriptive resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The easiest way do access API metadata programatically is to issue
``OPTIONS`` request to the API endpoint of choice. Example how to do that was
already presented in project's `README <https://github.com/swistakm/graceful>`_
file and :doc:`main documentation page <../readme>`. Using this built-in
capability of graceful's resources it should be definitely easy to populate your
HTML/JS based documentation portal with API metadata.

This is the preferred way to construct documentation portals for your API.
It has many advantages compared to documentation self-hosted within the same
application as your API service. Just to name a few:

* Documentation deployment is decoupled from deployment of your API service.
  Documentation portal can be stored in completely different project and
  does not even need to be hosted on the same machines as your API.
* Documentation portal may require completely different requirements that could
  be in conflict with you.
* API are often secured on different layers and using different authentication
  and authorization schemes. But documentations for such APIs are very often
  left open. If you keep them both separated it will allow you to reduce
  complexity of both projects.
* Changes to documentation layout and aesthetics do not require new deployments
  of whole service. This makes your operations more robust.

The popular `Swagger <http://swagger.io>`_ project is built with similar idea in
mind. If you like this project and are already familiar with it you should be
able to easily translate API metadata returned by graceful to format that is
accepted by Swagger.


Self-hosted documentation
~~~~~~~~~~~~~~~~~~~~~~~~~

Decoupling documentation portal from your API service is in many cases the most
reliable option. Anyway, there are many use cases where such approach migth be
simply incovenient. For instance, if you distribute your project as a
downloadable package (e.g. through PyPI) you may want to make it easily
accessible for new users without the need of bootstrapping mutliple processes
and services.

In such cases it might be reasonable to generate documentation in format that
is convenient to the user by the same process that serves your API requests.
The same features that allow you to easily access API metadata via ``OPTIONS``
requests allow you to introspect resources within your application process and
populate any kind of documents.

The most obvious approach is to create some HTML templates, fill them with
data retrieved from ``describe()`` method of each resource and serve them
directly to the user via HTTP.

Graceful can't do all of that out of the box (maybe in future) but general
process is very simple and does not require a lot of code. Additionally, you
have full control over what tools you want to use to build documentation.

In this section we will show how it could be done using some popular tools like
`Jinja <http://jinja.pocoo.org>`_ and
`python-hoedown <https://github.com/hhatto/python-hoedown>`_ but no one forces
you to use specific template language or text markup. Choose anything you like
and anything you are comfortable with. All code that is featured in this guide
is also available in the `demo <https://github.com/swistakm/graceful/tree/master/demo>`_
directory in the project repository.


Serving HTML and using Jinja templates in falcon
""""""""""""""""""""""""""""""""""""""""""""""""

Graceful isn't a full-flegded framework like Django or Flask. It is only
a toolkit that allows you to define REST APIs in a clean and convenient way.
Only that and nothing more.

Neither Graceful nor Falcon have built-in support for generating HTML responses
because it is not their main use case. But serving HTML isn't by any means
different from responding with JSON, XML, YAML, or any other content type.
What you need to do is to put your HTML to the body section of your response
and set proper value of the ``Content-Type`` header. Here is simple example
of falcon resource that serves some html:


.. code-block:: python

    import falcon

    class HtmlResource:
        def on_get(self, req, resp):
            resp.body = """
            <!DOCTYPE html>
            <html>
            <head><title>Hello World!</title></head>
            <body>
            <h1>Hello World!</h1>
            </body>
            </html>
            """
            resp.status = falcon.HTTP_200
            resp.content_type = 'text/html'

Of cource no one wants to generate documentation relying solely on
``str.format()``. One useful feature that many web frameworks offer is some
kind of templating engine that allows you to easily format different kinds of
documents. If you want to build beautiful documentation you will eventually
need a one. For the purpose of this example we will use Jinja that is usually
a very good choice and is very easy to start with.

In our documentation pages, we don't want to support any query string
parameters or define CRUD semenatics. So we don't need any of Graceful's
generic classes, parameters of serializers. Let's build simple falcon resource
that will allow us to respond with templated HTML response that may be
populated with some predefined (or dynamic) context:

.. code-block:: python

    from jinja2 import Environment, FileSystemLoader

    # environment allows us to load template files, 'templates' is a dir
    # where we want to store them
    env = Environment(loader=FileSystemLoader('templates'))

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

Assuming we have ``index.html`` Jinja template stored in the ``templates``
directory we can start to serve your first HTML from falcon by adding
``Templated`` resource instance to your app router:

.. code-block:: python

    api.add_route("/", Templated('index.html'))


Populating templates with resources metadata
""""""""""""""""""""""""""""""""""""""""""""

Once you are able to generate HTML pages from template it's time to populate
them with resource metadata. Every resource class instance in Graceful provides
``describe()`` method that returns dictionary that contains metadata with
information about it's resource structure (fields), accepted HTTP methods,
query string parameters, and so on. The general structure is as follows::

    {
        "details": ...           # => Resource class docstring
        "fields": {              # => Description of resource representation fields
            "<field_name>": {
                "details": ...,  # => Field definition 'details' string
                "label": ...,    # => Field definition 'label' string
                "spec": ...,     # => Additional specification tuple associated
                                 #    with specific field class. It is usualy
                                 #    standard name (e.g. ISO 639-2), and URL to its
                                 #    official documentation
                "type": ...,     # => Generic type name like 'string', 'bool', etc.
            },
            ...
        },
        "methods": [...],        # => List of accepted HTTP methods (uppercase)
        "name": "CatList",       # => Resource class name
        "params": {              # => Description of accepted query string params
            "<param_name>": {
                "default": ...,  # => Default parameter value
                "details": ...,  # => Param definition 'details' string
                "label": ...,
                "required": ..., # => Flag indicating if parameter is requires (bool)
                "spec": ...,     # => Additional specification tuple associated
                                 #    with specific param class. It is usualy
                                 #    standard name (e.g. ISO 639-2), and URL to its
                                 #    official documentation
                "type": "..."    # => Generic type name like 'string', 'bool', etc.
            },
        },
        "path": ...,             # => URI leading to resource (only available
                                 #    on OPTIONS requests)
        "type": ...,             # => General type of resource representation form.
                                 #    It may be "object" for single resource
                                 #    representation or "list" for endpoints that
                                 #    return list of resource representations.
    }

Knowing that resource descriptions have well defined and consistent structure
we can add them to predefined context of our ``Templated`` resource. Because
all API resources are always associated with their URIs (which are unique
per resource class), it is a good approach to group descriptions by their
URI templates from falcon router.

Let's assume we want to document Cats API example presented in
:doc:`main documentation page <../readme>`. Here is falcon's router
configuration that adds Cats API resources and additional templated
documentation resource that can render our service metadata in human readable
form:

.. code-block:: python

    api.add_route("/v1/cats/{cat_id}", V1.Cat())
    api.add_route("/v1/cats/", V1.CatList())
    api.add_route("/", Templated('index.html', {
        'endpoints': {
            "/v1/cats/": V1.CatList().describe(),
            "/v1/cats/{cat_id}": V1.Cat().describe(),
        }
    }))


For APIs that contain a lot of multiple resources it is always better to follow
"don't repeat yourself" principle:

.. code-block:: python

    api = application = falcon.API()

    endpoints = {
        "/v1/cats/{cat_id}": V1.Cat(),
        "/v1/cats/": V1.CatList(),
    }

    for uri, endpoint in endpoints:
        api.add_route(uri, endpoints)

    api.add_route("/", Templated('index.html', {
        'endpoints': {
            uri: endpoint.describe()
            for uri, endpoint
            in endpoints.items()
        }
    }))


The last thing you need to do is to create a template that will be used to
render your documentation. Here is a minimal Jinja template for Cats API that
provides general overview on the API structure with plain HTML and without any
fancy styling:


.. code-block:: jinja

    <!DOCTYPE html>
    <html>
    <head lang="en">
        <meta charset="UTF-8">
        <title>Cats API</title>
    </head>
    <body>

    <h1>Cats API documentation</h1>

    <p> Welcome to Cats API documentation </p>

    {% for uri, endpoint in endpoints.items() %}
        <h2>{{ endpoint.name }}: <code>{{ uri }}</code></h2>

        <p>
            <strong>Accepted methods:</strong>
            <code>{{ endpoint.methods }}</code>
        </p>

        <p> {{ endpoint.details }}</p>

        <h3>Accepted params</h3>
        {% if endpoint.params %}
            <ul>
                {% for name, param in endpoint.params.items() %}
                <li>{{ name }} ({{ param.type }}): {{ param.details }}</li>
                {% endfor %}
            </ul>
        {% endif %}

        <h3>Accepted fields</h3>
        {% if endpoint.fields %}
            <ul>
                {% for name, field in endpoint.fields.items() %}
                <li>{{ name }} ({{ field.type }}): {{ field.details }}</li>
                {% endfor %}
            </ul>
        {% endif %}
    {% endfor %}
    </body>
    </html>


Formatting resource class docstrings
""""""""""""""""""""""""""""""""""""

Building good service documentation is not an easy task but Graceful tries to
make it at least a bit easier by providing you with some tools to introspect
your service. Thanks to this you can take resource metadata and convert it to
human readable form.

But your work does not end on providing the list of acceptable fields and
parameters. Very often you may need to provide some more information about
specific resource type like specific limits, usage example or rationale behind
your design decisions. The best place to do that is the resource docstring
that is always included in the result of ``describe()`` method call. This is
very convenient way of managing even large parts of your documentation.

But when docstrings get longer and longer it is good idea to add a bit more
structure to them instead of keeping them unformatted. A good idea is to use
some lightweight markup language that is easy-to-read in plain text (so it is
easy to edit by developer) but provides you with enough rendering capabilities
to make your documentation look good for actual API user. A very popular choice
for a lightweight markup is  `Markdown <https://en.wikipedia.org/wiki/Markdown>`_.

It seems that everyone loves Markdown, but apparently there is no Markdown
parser (at least availaible in Python) that would not suck terribly in some of
its aspects. Anyway, Python binding to
`hoedown <https://github.com/hoedown/hoedown>`_ (that is fork of sundown, that
is fork of upskirt, that is now a libsoldout...) has acceptable quality and can
be successfully used for that purpose.

The best news is that it is insanely easy to integrate it with Jinja. The only
thing you need to do is to create new template filter that will allow you to
convert any string to HTML inside of you template. It could be something like
following:

.. code-block:: python

    import hoedown
    from jinja2 import Environment, FileSystemLoader

    # environment allows us to load template files, 'templates' is a dir
    # where we want to store them
    env = Environment(loader=FileSystemLoader('templates'))

    md = hoedown.Markdown(
        CustomRenderer(),
        extensions=hoedown.EXT_FENCED_CODE | hoedown.EXT_HIGHLIGHT
    )

    def markdown_filter(data):
        return md.render(data)

    env.filters['markdown'] = markdown_filter

With such definition you can use your new filter anywhere in template
where you expect string to be multiline Markdown markup:

.. code-block:: jinja

    {% for uri, endpoint in endpoints.items() %}
        <h2>{{ endpoint.name }}: <code>{{ uri }}</code></h2>

        <p> {{ endpoint.details|markdown }}</p>
    {% endfor %}

You can also use that technique to format multiline strings supplied
as ``details`` arguments to fields and parameters definitions. Graceful
will properly strip excesive leading whitespaces from them so you can
easily use any indentation-sensitive markup language (like reStructuredText).
