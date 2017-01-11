import pytest

from falcon import Request, Response
from falcon.testing import create_environ


@pytest.fixture
def req():
    """Simple GET Request fixture."""
    env = create_environ()
    return Request(env)


@pytest.fixture
def resp():
    """Simple empty Response fixture."""
    return Response()
