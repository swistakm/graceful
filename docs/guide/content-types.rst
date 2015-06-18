Content types
-------------

graceful currently talks only JSON. If you want to support other
content-types then the only way is to override
:meth:`BaseResource.make_body`,
:meth:`BaseResource.require_representation` and optionally
:meth:`BaseResource.on_options` etc. methods. Suggested way would be do
create a class mixin that can be added to every of your resources but ideally
an contribution that adds reasonable content negotiation and pluggable
content-type serialization.

