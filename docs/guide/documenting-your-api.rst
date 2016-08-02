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
