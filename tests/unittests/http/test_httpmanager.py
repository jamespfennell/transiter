import datetime
import unittest
import unittest.mock as mock

from transiter.general import exceptions
from transiter.http import httpmanager
from transiter.services import links
from .. import testutil


class TestHttpManager(testutil.TestCase(httpmanager), unittest.TestCase):

    def test_all_exceptions_inherit_from_transiter_exceptions(self):
        """[HTTP Manager] Ensure every exception inherits from TransiterException"""
        for exception_variable in exceptions.__dict__.values():
            try:
                if not issubclass(exception_variable, Exception):
                    continue
            except TypeError:
                # NOTE: this happens if exception_variable is not a class.
                continue
            self.assertTrue(
                issubclass(exception_variable, exceptions._TransiterException)
            )

    def test_all_exceptions_have_http_status(self):
        """[HTTP Manager] Ensure every exception has a HTTP status"""
        for transiter_exception in exceptions._TransiterException.__subclasses__():
            print('Testing', transiter_exception)
            self.assertTrue(
                transiter_exception in
                httpmanager._exception_type_to_http_status
            )




"""

RAW_RESPONSE = {'key': 'value'}
JSON_RESPONSE = 'JsonResponse'

def mock_convert_for_http(data):
    if data == RAW_RESPONSE:
        return JSON_RESPONSE
    raise NotImplementedError

#responsemanager.jsonutil.convert_for_http = mock_convert_for_http


class TestGetRequests(unittest.TestCase):

    @mock.patch('transiter.http.responsemanager.convert_to_json')
    def test_content(self, convert_to_json):
        convert_to_json.side_effect = mock_convert_for_http
        @httpmanager.http_get_response
        def response():
            return RAW_RESPONSE

        content, http_code, __ = response()

        self.assertEqual(content, JSON_RESPONSE)
        self.assertEqual(http_code, httpmanager.HTTP_200_OK)


class TestPostRequests(unittest.TestCase):

    @mock.patch('transiter.http.responsemanager.convert_to_json')
    def test_content(self, convert_to_json):
        convert_to_json.side_effect = mock_convert_for_http
        @httpmanager.http_get_response
        def response():
            return RAW_RESPONSE

        content, http_code, __ = response()

        self.assertEqual(content, JSON_RESPONSE)
        self.assertEqual(http_code, httpmanager.HTTP_200_OK)


class TestPutRequests(unittest.TestCase):

    def test_put(self):
        @httpmanager.http_put_response
        def response():
            return True


        content, http_code, __ = response()

        self.assertEqual(content, '')
        self.assertEqual(http_code, httpmanager.HTTP_201_CREATED)

    def test_not_put(self):
        @httpmanager.http_put_response
        def response():
            return False

        content, http_code, __ = response()

        self.assertEqual(content, '')
        self.assertEqual(http_code, httpmanager.HTTP_204_NO_CONTENT)


class TestDeleteRequests(unittest.TestCase):

    def test_delete(self):
        @httpmanager.http_delete_response
        def response():
            return None

        content, http_code, __ = response()

        self.assertEqual(content, '')
        self.assertEqual(http_code, httpmanager.HTTP_204_NO_CONTENT)


class TestExceptionHandling(unittest.TestCase):

    def _response_dectorators(self):
        return [
            httpmanager.http_get_response,
            httpmanager.http_put_response,
            httpmanager.http_delete_response
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
        self._test_handled_exception(
            exceptions.IdNotFoundError,
            httpmanager.HTTP_404_NOT_FOUND)

    def test_permission_denied(self):
        self._test_handled_exception(
            exceptions.AccessDenied,
            httpmanager.HTTP_403_FORBIDDEN)

    def test_unknown_permission_level(self):
        self._test_handled_exception(
            exceptions.InvalidPermissionsLevelInRequest,
            httpmanager.HTTP_400_BAD_REQUEST)

    def test_unhandled_exception(self):
        # TODO(enable this test)
        return
        for response_decorator in self._response_dectorators():
            @response_decorator
            def response():
                raise Exception

            content, http_code, __ = response()

            self.assertEqual(content, '')
            self.assertEqual(http_code, httpmanager.HTTP_500_SERVER_ERROR)


class TestJsonConversion(unittest.TestCase):

    LINK = 'Link'
    TIMESTAMP = 300


    def test_datetime(self):
        fake_datetime = datetime.datetime(2018, 10, 30, 0, 0, 0)
        expected = httpmanager._convert_to_json_str(fake_datetime.timestamp())
        actual = httpmanager._convert_to_json_str(fake_datetime)
        self.assertEqual(actual, expected)

    def _test_link(self):
        class FakeLink(links.Link):
            def __init__(self):
                pass
            def url(inner):
                return self.LINK

        fake_link = FakeLink()
        actual = httpmanager._convert_to_json_str(fake_link)
        expected = httpmanager._convert_to_json_str(self.LINK)
        self.assertEqual(actual, expected)

    def test_unknown_object(self):
        class RandomClass:
            def __init__(self):
                pass

        random_object = RandomClass()
        self.assertRaises(TypeError, httpmanager._convert_to_json_str, random_object)


"""
