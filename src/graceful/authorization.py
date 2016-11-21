# -*- coding: utf-8 -*-
from functools import wraps
from falcon import hooks, HTTPUnauthorized


def _before(hook):
    """Metadata preserving version of ``falcon.hooks.before``.

    Args:
        hook: actual hook version.

    Returns: falcon hook decorator.
    """
    return wraps(hook)(hooks.before(hook))


@_before
def authentication_required(req, resp, resource, uri_kwargs):
    """Ensure that user is authenticated otherwise return ``401 Unauthorized``.

    If request fails to authenticate this authorization hook will also
    include list of ``WWW-Athenticate`` challenges.

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
