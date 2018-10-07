import unittest
import unittest.mock as mock
from transiter.endpoints import responsemanager
from transiter.services import exceptions

RAW_RESPONSE = {'key': 'value'}
JSON_RESPONSE = 'JsonResponse'

def mock_convert_for_http(data):
    if data == RAW_RESPONSE:
        return JSON_RESPONSE
    raise NotImplementedError


#responsemanager.jsonutil.convert_for_http = mock_convert_for_http


class TestGetRequests(unittest.TestCase):

    @mock.patch('transiter.endpoints.responsemanager.jsonutil')
    def test_content(self, jsonutil):
        jsonutil.convert_for_http = mock_convert_for_http
        @responsemanager.http_get_response
        def response():
            return RAW_RESPONSE

        content, http_code, __ = response()

        self.assertEqual(content, JSON_RESPONSE)
        self.assertEqual(http_code, responsemanager.HTTP_200_OK)


class TestPostRequests(unittest.TestCase):

    @mock.patch('transiter.endpoints.responsemanager.jsonutil')
    def test_content(self, jsonutil):
        jsonutil.convert_for_http = mock_convert_for_http
        @responsemanager.http_get_response
        def response():
            return RAW_RESPONSE

        content, http_code, __ = response()

        self.assertEqual(content, JSON_RESPONSE)
        self.assertEqual(http_code, responsemanager.HTTP_200_OK)

class TestPutRequests(unittest.TestCase):

    def test_put(self):
        @responsemanager.http_put_response
        def response():
            return True


        content, http_code, __ = response()

        self.assertEqual(content, '')
        self.assertEqual(http_code, responsemanager.HTTP_201_CREATED)

    def test_not_put(self):
        @responsemanager.http_put_response
        def response():
            return False

        content, http_code, __ = response()

        self.assertEqual(content, '')
        self.assertEqual(http_code, responsemanager.HTTP_204_NO_CONTENT)


class TestDeleteRequests(unittest.TestCase):

    def test_delete(self):
        @responsemanager.http_delete_response
        def response():
            return None

        content, http_code, __ = response()

        self.assertEqual(content, '')
        self.assertEqual(http_code, responsemanager.HTTP_204_NO_CONTENT)


class TestExceptionHandling(unittest.TestCase):

    def _response_dectorators(self):
        return [
            responsemanager.http_get_response,
            responsemanager.http_put_response,
            responsemanager.http_delete_response
        ]

    def test_handled_exceptions(self):
        for response_decorator in self._response_dectorators():
            @response_decorator
            def response():
                raise exceptions.IdNotFoundError

            content, http_code, __ = response()

            self.assertEqual(content, '')
            self.assertEqual(http_code, responsemanager.HTTP_404_NOT_FOUND)

    def test_unhandled_exception(self):
        # TODO(enable this test)
        return
        for response_decorator in self._response_dectorators():
            @response_decorator
            def response():
                raise Exception

            content, http_code, __ = response()

            self.assertEqual(content, '')
            self.assertEqual(http_code, responsemanager.HTTP_500_SERVER_ERROR)