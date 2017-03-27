# -*- coding: utf-8 -*-
from functools import wraps
from falcon import hooks, HTTPUnauthorized
import falcon.version

# todo: consider moving to `compat` module if we have to use more compat code
FALCON_VERSION = tuple(map(int, falcon.version.__version__.split('.')))


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

    .. versionadded:: 0.4.0
    """
    if 'user' not in req.context:
        args = ["Unauthorized", "This resource requires authentication"]

        # compat: falcon >= 1.0.0 requires the list of challenges
        if FALCON_VERSION >= (1, 0, 0):
            args.append(req.context.get('challenges', []))

        raise HTTPUnauthorized(*args)
