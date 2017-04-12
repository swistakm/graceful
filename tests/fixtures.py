from types import SimpleNamespace as BaseSimpleNamespace
from collections import defaultdict
from functools import partial

import pytest

from falcon import Request, Response
from falcon.testing import create_environ

# compat: SimpleNamespace depends on of built-in sys module (the type of
#         type of sys.implementation variable) and may be implementation
#         dependent. For instance, in Python3.3 it does not have its own
#         __eq__ method implementation so two equivalent namespaces do not
#         compare as equal ones.
if BaseSimpleNamespace() == BaseSimpleNamespace():
    SimpleNamespace = BaseSimpleNamespace
else:
    class SimpleNamespace(BaseSimpleNamespace):
        """Extended ``SimpleNamespace`` implementation for Python3.3."""

        def __eq__(self, other):
            """Check if two namesapces have equal content."""
            return self.__dict__ == other.__dict__


@pytest.fixture
def req():
    """Simple GET Request fixture."""
    env = create_environ()
    return Request(env)


@pytest.fixture
def resp():
    """Simple empty Response fixture."""
    return Response()


@pytest.fixture(
    params=[
        dict,
        SimpleNamespace,
        # note: this is not a class per-se but acts like a one
        partial(defaultdict, str)
    ],
)
def instance_class(request):
    """Instance class that may be used as a instance_factory attribute.

    This fixture helps testing serializers.
    """
    return request.param
