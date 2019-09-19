import datetime
import unittest

from transiter import exceptions
from transiter.http import httpmanager
from transiter.services import links
from .. import testutil


# NOTE: Most of the test coverage of the HTTP manager comes from the endpoint
# testing in which the HTTP manager is not mocked. This testing class is
# designed to capture a few of the cases no captured in the endpoint testing.


class TestHttpManager(testutil.TestCase(httpmanager), unittest.TestCase):
    FAKE_URL = "http://www.transiter.io/entity"
    TIMESTAMP = 24536456

    def setUp(self):
        self.flask = self.mockImportedModule(httpmanager.flask)

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
            print("Testing", transiter_exception)
            self.assertTrue(
                transiter_exception in httpmanager._exception_type_to_http_status
            )

    def test_unexpected_error(self):
        """[HTTP Manager] Unexpected error"""

        @httpmanager.http_response()
        def bad_endpoint():
            raise ValueError

        __, status, __ = bad_endpoint()

        self.assertEqual(httpmanager.HttpStatus.INTERNAL_SERVER_ERROR, status)

    def test_json_serialization__links(self):
        """[HTTP Manager] JSON serialization of Links"""

        class FakeLink(links.Link):
            pass

        @httpmanager.link_target(FakeLink)
        def entity():
            pass

        self.flask.request.headers = {}
        self.flask.url_for.return_value = self.FAKE_URL

        actual_url = httpmanager._transiter_json_serializer(FakeLink())

        self.assertEqual(self.FAKE_URL, actual_url)

        self.flask.url_for.assert_called_once_with(
            "{}.{}".format(__name__, entity.__name__), _external=True
        )

    def test_json_serialization__links_with_host(self):
        """[HTTP Manager] JSON serialization of Links with custom host"""

        class FakeLink(links.Link):
            pass

        @httpmanager.link_target(FakeLink)
        def entity():
            pass

        self.flask.request.headers = {"X-Transiter-Host": "myhost"}
        self.flask.url_for.return_value = self.FAKE_URL

        actual_url = httpmanager._transiter_json_serializer(FakeLink())

        self.assertEqual("myhost" + self.FAKE_URL, actual_url)

        self.flask.url_for.assert_called_once_with(
            "{}.{}".format(__name__, entity.__name__), _external=False
        )

    def test_json_serialization__datetimes(self):
        """[HTTP Manager] JSON serialization of datetimes"""

        dt = datetime.datetime.fromtimestamp(self.TIMESTAMP)

        actual_timestamp = httpmanager._transiter_json_serializer(dt)

        self.assertEqual(self.TIMESTAMP, actual_timestamp)

    def test_json_serialization__unknown_object(self):
        """[HTTP Manager] JSON serialization failure given unknown object"""

        self.assertRaises(
            TypeError, lambda: httpmanager._transiter_json_serializer(unittest.TestCase)
        )
