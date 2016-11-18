# -*- coding: utf-8 -*-
from falcon import hooks, HTTPUnauthorized


@hooks.before
def is_authenticated(req, resp, resource, uri_kwargs):
    """Ensure that user is authenticated otherwise return ``401 Unauthorized``.

    Args:
        req (falcon.Request): the request object.
        resp (falcon.Response): the response object.
        resource (object): the resource object.
        uri_kwargs (dict): keyword arguments from the URI template.

    """
    if 'user' not in req.context:
        raise HTTPUnauthorized(
            "Unauthorized",
            "This resource requires authentication",
            req.context.get('challenges', [])
        )
