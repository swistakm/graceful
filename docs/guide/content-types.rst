Content types
-------------

``graceful`` currently talks only JSON. If you want to support other
content-types then the only way is to override ``Resource.on_get()``,
``Resource.on_options()`` etc. methods. Suggested way would be do create a
class mixin that can be added to every of your resources.

