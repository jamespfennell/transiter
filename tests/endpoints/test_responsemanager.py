import unittest
import unittest.mock as mock
from transiter.endpoints import responsemanager, permissionsvalidator
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
        """[Response manager] Get request"""
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
        """[Response manager] Post request"""
        jsonutil.convert_for_http = mock_convert_for_http
        @responsemanager.http_get_response
        def response():
            return RAW_RESPONSE

        content, http_code, __ = response()

        self.assertEqual(content, JSON_RESPONSE)
        self.assertEqual(http_code, responsemanager.HTTP_200_OK)

class TestPutRequests(unittest.TestCase):

    def test_put(self):
        """[Response manager] Put request with changes"""
        @responsemanager.http_put_response
        def response():
            return True


        content, http_code, __ = response()

        self.assertEqual(content, '')
        self.assertEqual(http_code, responsemanager.HTTP_201_CREATED)

    def test_not_put(self):
        """[Response manager] Put request with no changes"""
        @responsemanager.http_put_response
        def response():
            return False

        content, http_code, __ = response()

        self.assertEqual(content, '')
        self.assertEqual(http_code, responsemanager.HTTP_204_NO_CONTENT)


class TestDeleteRequests(unittest.TestCase):

    def test_delete(self):
        """[Response manager] Delete request"""
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

    def _test_handled_exception(self, exception, expected_http_code):
        for response_decorator in self._response_dectorators():
            @response_decorator
            def response():
                raise exception

            content, http_code, __ = response()

            self.assertEqual(content, '')
            self.assertEqual(http_code, expected_http_code)
        return True

    def test_id_not_found(self):
        """[Response manager] Entity not found error response"""
        self._test_handled_exception(
            exceptions.IdNotFoundError,
            responsemanager.HTTP_404_NOT_FOUND)

    def test_permission_denied(self):
        """[Response manager] Access denied error response"""
        self._test_handled_exception(
            permissionsvalidator.AccessDenied,
            responsemanager.HTTP_403_FORBIDDEN)

    def test_unknown_permission_level(self):
        """[Response manager] Unknown permission level error response"""
        self._test_handled_exception(
            permissionsvalidator.UnknownPermissionsLevelInRequest,
            responsemanager.HTTP_400_BAD_REQUEST)

    def test_unhandled_exception(self):
        """[Response manager] Unhandled exception response"""
        # TODO(enable this test)
        return
        for response_decorator in self._response_dectorators():
            @response_decorator
            def response():
                raise Exception

            content, http_code, __ = response()

            self.assertEqual(content, '')
            self.assertEqual(http_code, responsemanager.HTTP_500_SERVER_ERROR)