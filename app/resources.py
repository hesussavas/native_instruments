import logging
from typing import Tuple

from flask_restful import Resource, abort, reqparse

from app.redis_init import redis_client
from app.utils import validate_expire_in

logger = logging.getLogger(__name__)

# arguments for PUT request defined
parser = reqparse.RequestParser()
parser.add_argument('key')
parser.add_argument('value')
parser.add_argument('expire_in')

# 'filter' argument for GET defined
parser.add_argument('filter')


class KeyValuePairListResource(Resource):
    """
    Represents the resource which will process requests on the '/keys/' endpoint
    Supported HTTP methods: GET, PUT, DELETE
    """

    def get(self) -> Tuple[str, int]:
        """
        Gets all keys and values.
        If there is 'filter' query-param, then it's possible to filter the keys with the pattern presented
        as a 'filter' param's value. This value could contain wildcard symbols:
          '*' - matches any string, including the empty string
          '$' - matches any single character (we use $ instead of ?, cause it's impossible to use ? in
          GET query-string. We will convert $ into ? in the code, so that the pattern is glob-style complaint).
          *For example:*
            - 'te$t' matches test, text and tent
            - 'te*t' matches terrorist and tet

        :return: dict with key-value pairs or 404 status code if there is no keys for the specified pattern
        """
        args = parser.parse_args()
        # by default we will use '*' pattern if nothing provided in 'filter' argument
        keys_pattern = args.get('filter') or "*"
        # replace $ symbols with ? so that pattern could be glob-style complaint and be used by redis
        keys_pattern_converted = keys_pattern.replace("$", "?")

        all_keys = [r.decode("utf-8") for r in redis_client.keys(keys_pattern_converted)]
        if not all_keys:
            logger.warning(f"No keys for such pattern: {keys_pattern}")
            abort(404, message=f"No keys for such pattern: {keys_pattern}")
        else:
            all_values = (r.decode("utf-8") for r in redis_client.mget(all_keys))
            return dict(zip(all_keys, all_values)), 200

    def put(self) -> Tuple[str, int]:
        """
        Sets a value for a specific key. Both key and value should be presented inside the body of the request.
        By default, ttl for the key is infinite.
        Also supports 'expire_in' query-string argument, which will use the value of the argument as a ttl for the key.
        Expected that value for 'expire_in' is in seconds.
        :return: dict with key and value or 400 status code if there is invalid arguments provided
        """
        args = parser.parse_args()
        # get body arguments
        key, value = args.get('key'), args.get('value')
        # validate their presence
        if not all([key, value]):
            logger.warning(f"Bad or empty arguments: key='{key}', value='{value}'")
            abort(400, message="You should provide 'key' and 'value' arguments")
        # set the key
        redis_client.set(key, value)

        # if there is query argument 'expire_in', then add expiration to the key
        expire_in = args.get('expire_in')
        if expire_in:
            try:
                validate_expire_in(expire_in)
            except ValueError:
                logger.warning(f"Invalid 'expire_in' value: {expire_in}")
                abort(400, message="Invalid 'expire_in' value. Must be numeric")

            redis_client.expire(key, expire_in)

        return {key: value}, 201

    def delete(self) -> Tuple[str, int]:
        """
        Deletes all the values and keys. Please, use with care.
        :return: Empty body and 204 status code.
        """
        redis_client.flushall()
        return "", 204


class KeyValuePairResource(Resource):
    """
    Represents the resource which will process requests on the '/keys/{id}' endpoint
    Supported HTTP methods: HEAD, GET, DELETE
    """

    # flask will use the same method for HEAD.
    def get(self, key: str) -> Tuple[str, int]:
        """
        Gets a value of the specified key. This method will also be called for HEAD requests (flask's feature)
        :param key: string representing key
        :return: value of the key and 200 status code or 404 status code if there is no such key.
        """
        value = redis_client.get(key)
        if value:
            return value.decode("utf-8"), 200
        else:
            logger.warning(f"Key doesn't exist: {key}")
            abort(404, message="Key doesn't exist")

    def delete(self, key: str) -> Tuple[str, int]:
        """
        Delete a value and specified key.
        :param key: string representing key
        :return: empty body and 204 status code
        """
        redis_client.delete(key)
        return '', 204
