import doctest
import unittest
from unittest.mock import patch

from app import run, utils


class TestCaseWithMockedRedis(unittest.TestCase):
    """Base TestCase class with redis mocking functionality"""

    def setUp(self):
        # patch where the object is looked up rather than defined
        self.patch = patch('app.resources.redis_client')
        # run.create_app() also uses redis - we need to start patching here
        self.mocked_redis = self.patch.start()

        # initialize app with testing config
        _app = run.create_app("app.config.TestingConfig")
        self.client = _app.test_client()

    def tearDown(self):
        # don't forget to un-patch
        self.patch.stop()


class TestKeyValuePairListResource(TestCaseWithMockedRedis):
    """ Test cases for methods described in KeyValuePairListResource - e.g. requests to url 'api/v1/keys/' """

    def test_get_no_keys_for_default_pattern(self):
        response = self.client.get('api/v1/keys/')

        self.assertEqual(404, response.status_code)
        self.mocked_redis.keys.assert_called_with("*")

    def test_get_all_existing_keys(self):
        self.mocked_redis.keys.return_value = [b'test_key1']
        self.mocked_redis.mget.return_value = [b'test_value1']
        response = self.client.get('api/v1/keys/')

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.get_json(), {"test_key1": "test_value1"})
        # check KEYS command was called with default arg.
        self.mocked_redis.keys.assert_called_with("*")
        self.mocked_redis.mget.assert_called_with(["test_key1"])

    def test_get_existing_keys_by_pattern(self):
        self.mocked_redis.keys.return_value = [b'test_key1', b'test_key2']
        self.mocked_redis.mget.return_value = [b'test_value1', b'test_value2']
        response = self.client.get('api/v1/keys/?filter=$est')
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.get_json(), {"test_key1": "test_value1", "test_key2": "test_value2"})
        # check KEYS command was called with specified pattern and $ symbol was exchanged with ?.
        self.mocked_redis.keys.assert_called_with("?est")
        self.mocked_redis.mget.assert_called_with(["test_key1", "test_key2"])

    def test_put_bad_args(self):
        response = self.client.put('api/v1/keys/', data=dict())
        self.assertEqual(400, response.status_code)

    def test_put_without_expiration(self):
        response = self.client.put('api/v1/keys/', data=dict(key="test_key", value="test_value"))
        self.assertEqual(201, response.status_code)
        self.assertEqual({"test_key": "test_value"}, response.get_json())
        self.mocked_redis.set.assert_called_with("test_key", "test_value")

    def test_put_expiration_with_bad_arg(self):
        response = self.client.put('api/v1/keys/', data=dict(key="test_key", value="test_value", expire_in="42sec"))
        self.assertEqual(400, response.status_code)
        self.mocked_redis.set.assert_called_with("test_key", "test_value")

    def test_put_expiration_with_valid_arg(self):
        response = self.client.put('api/v1/keys/', data=dict(key="test_key", value="test_value", expire_in=42))
        self.assertEqual(201, response.status_code)
        self.assertEqual({"test_key": "test_value"}, response.get_json())
        self.mocked_redis.set.assert_called_with("test_key", "test_value")
        self.mocked_redis.expire.assert_called_with("test_key", "42")

    def test_delete_all(self):
        response = self.client.delete('api/v1/keys/')
        self.assertEqual(204, response.status_code)
        self.mocked_redis.flushall.assert_called()


class TestKeyValuePairResource(TestCaseWithMockedRedis):
    """ Test cases for methods described in KeyValuePairResource - e.g. requests to url 'api/v1/keys/{id}' """

    def test_get_value_by_key_negative(self):
        self.mocked_redis.get.return_value = None
        response = self.client.get('api/v1/keys/42IDDQD')

        self.assertEqual(404, response.status_code)
        self.mocked_redis.get.assert_called_with("42IDDQD")

    def test_get_value_by_key_positive(self):
        self.mocked_redis.get.return_value = b'test_value1'
        response = self.client.get('api/v1/keys/42')

        self.assertEqual(200, response.status_code)
        self.assertEqual("test_value1", response.get_json())
        self.mocked_redis.get.assert_called_with("42")

    def test_head_value_by_key_negative(self):
        self.mocked_redis.get.return_value = None
        response = self.client.head('api/v1/keys/42IDDQD')

        self.assertEqual(404, response.status_code)
        self.mocked_redis.get.assert_called_with("42IDDQD")

    def test_head_value_by_key_positive(self):
        self.mocked_redis.get.return_value = b'test_value1'
        response = self.client.head('api/v1/keys/42')

        self.assertEqual(200, response.status_code)
        self.mocked_redis.get.assert_called_with("42")
        # empty body in response
        self.assertEqual(b"", response.data)

    def test_delete_value_by_key(self):
        response = self.client.delete('api/v1/keys/fcuk')

        self.assertEqual(204, response.status_code)
        self.mocked_redis.delete.assert_called_with("fcuk")
        # empty body in response
        self.assertEqual(b"", response.data)


# Run doctest together with unittests
def load_tests(loader, tests, pattern):
    """ Will add doctests from the module to the unittest suite and run them together."""
    tests.addTests(doctest.DocTestSuite(utils))
    return tests


if __name__ == '__main__':
    unittest.main()
