import hashlib

from redis import StrictRedis as Redis
import falcon

from graceful.resources.generic import Resource
from graceful.authentication import KeyValueUserStorage, Token, Basic
from graceful.authorization import authentication_required


@authentication_required
class Me(Resource, with_context=True):
    def retrieve(self, params, meta, context):
        return context.get('user')


auth_storage = KeyValueUserStorage(Redis())


@auth_storage.hash_identifier.register(Basic)
def _basic(identified_with, identifier):
    return ":".join((
        identifier[0],
        hashlib.sha1(identifier[1].encode()).hexdigest()
    ))


@auth_storage.hash_identifier.register(Token)
def _token(identified_with, identifier):
    return hashlib.sha1(identifier[1].encode()).hexdigest()

api = application = falcon.API(
    middleware=[
        Token(auth_storage),
        Basic(auth_storage),
    ]
 )

api.add_route('/me/', Me())
