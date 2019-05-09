import unittest
import unittest.mock as mock

from transiter.http import permissions
from transiter import exceptions
from transiter.http import flaskapp
from transiter.http.endpoints import (
    routeendpoints,
    stopendpoints,
    tripendpoints,
    systemendpoints,
    feedendpoints,
)
from ... import testutil


class _TestEndpoints(unittest.TestCase):
    SYSTEM_ID = "1"
    ROUTE_ID = "2"
    TRIP_ID = "3"
    STOP_ID = "4"
    FEED_ID = "5"
    FEED_UPDATE_ID = "6"
    SERVICE_RESPONSE = {"A": "B"}
    JSON_RESPONSE = "C"
    SERVICE_NO_RESPONSE = True
    JSON_NO_RESPONSE = ""

    def setUp(self):
        self.setUpSuper()

    def setUpSuper(self):
        patcher = mock.patch("transiter.http.httpmanager._convert_to_json_str")
        self.convert_to_json = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch.object(permissions, "ensure")
        self.ensure = patcher.start()
        self.addCleanup(patcher.stop)

    def _test_endpoint(
        self,
        endpoint_function,
        service_function,
        args,
        service_response,
        endpoint_response,
    ):

        service_function.return_value = service_response
        if endpoint_response != "":
            self.convert_to_json.return_value = endpoint_response

        (actual, __, __) = endpoint_function(*args)

        self.assertEqual(actual, endpoint_response)
        if endpoint_response != "":
            self.convert_to_json.assert_called_once_with(service_response)
        service_function.assert_called_once_with(*args)

    def _test_response_endpoint(self, endpoint_function, service_function, args=()):
        self._test_endpoint(
            endpoint_function,
            service_function,
            args,
            self.SERVICE_RESPONSE,
            self.JSON_RESPONSE,
        )

    def _test_no_response_endpoint(self, endpoint_function, service_function, args=()):
        self._test_endpoint(
            endpoint_function,
            service_function,
            args,
            self.SERVICE_NO_RESPONSE,
            self.JSON_NO_RESPONSE,
        )

    def _test_not_implemented_endpoint(self, endpoint_function, args=()):
        (actual, http_code, __) = endpoint_function(*args)
        self.assertEqual(actual, "")
        self.assertEqual(http_code, 501)

    def _test_access_denied(self, endpoint_function, args=()):
        (actual, http_code, __) = endpoint_function(*args)
        self.assertEqual(http_code, 403)


class TestFeedEndpoints(testutil.TestCase(feedendpoints), _TestEndpoints):
    def setUp(self):
        self.setUpSuper()
        self.feedservice = self.mockImportedModule(feedendpoints.feedservice)

    def test_list_all_in_system(self):
        """[Feed endpoints] List all feeds in a system"""
        self._test_response_endpoint(
            feedendpoints.list_all_in_system,
            self.feedservice.list_all_in_system,
            (self.SYSTEM_ID,),
        )

    def test_list_all_in_system__no_permission(self):
        """[Feed endpoints] List all feeds in a system - access denied"""
        self.ensure.side_effect = exceptions.AccessDenied
        self._test_access_denied(feedendpoints.list_all_in_system, (self.SYSTEM_ID,))

    def test_get_in_system_by_id(self):
        """[Feed endpoints] Get a specific feed in a system"""
        self._test_response_endpoint(
            feedendpoints.get_in_system_by_id,
            self.feedservice.get_in_system_by_id,
            (self.SYSTEM_ID, self.ROUTE_ID),
        )

    def test_get_in_system_by_id__no_permission(self):
        """[Feed endpoints] Get a specific feed in a system - access denied"""
        self.ensure.side_effect = exceptions.AccessDenied
        self._test_access_denied(
            feedendpoints.get_in_system_by_id, (self.SYSTEM_ID, self.FEED_ID)
        )

    def test_create_feed_update(self):
        """[Feed endpoints] Create a new feed update for a specific feed"""
        self._test_response_endpoint(
            feedendpoints.create_feed_update,
            self.feedservice.create_feed_update,
            (self.SYSTEM_ID, self.FEED_ID),
        )

    def test_create_feed_update__access_denied(self):
        """[Feed endpoints] Create a new feed update for a specific feed - access denied"""
        self.ensure.side_effect = exceptions.AccessDenied
        self._test_access_denied(
            feedendpoints.get_in_system_by_id, (self.SYSTEM_ID, self.ROUTE_ID)
        )

    def test_list_updates_in_feed(self):
        """[Feed endpoints] List all updates for a specific feed"""
        self._test_response_endpoint(
            feedendpoints.list_updates_in_feed,
            self.feedservice.list_updates_in_feed,
            (self.SYSTEM_ID, self.FEED_ID),
        )

    def test_list_updates_in_feed__access_denied(self):
        """[Feed endpoints] List all updates for a specific feed - access denied"""
        self.ensure.side_effect = exceptions.AccessDenied
        self._test_access_denied(
            feedendpoints.get_in_system_by_id, (self.SYSTEM_ID, self.ROUTE_ID)
        )


class TestRouteEndpoints(testutil.TestCase(routeendpoints), _TestEndpoints):
    def setUp(self):
        self.setUpSuper()
        self.routeservice = self.mockImportedModule(routeendpoints.routeservice)

    def test_list_all_in_system(self):
        """[Route endpoints] List all routes in a system"""
        self._test_response_endpoint(
            routeendpoints.list_all_in_system,
            self.routeservice.list_all_in_system,
            self.SYSTEM_ID,
        )

    def test_get_in_system_by_id(self):
        """[Route endpoints] Get a specific route in a system"""
        self._test_response_endpoint(
            routeendpoints.get_in_system_by_id,
            self.routeservice.get_in_system_by_id,
            (self.SYSTEM_ID, self.ROUTE_ID),
        )


class TestStopEndpoints(testutil.TestCase(stopendpoints), _TestEndpoints):
    def setUp(self):
        self.setUpSuper()
        self.stopservice = self.mockImportedModule(stopendpoints.stopservice)

    def test_list_all_in_route(self):
        """[Stop endpoints] List all stop in a system"""
        self._test_response_endpoint(
            stopendpoints.list_all_in_system,
            self.stopservice.list_all_in_system,
            self.SYSTEM_ID,
        )

    def test_get_in_route_by_id(self):
        """[Stop endpoints] Get a specific stop in a system"""
        self._test_response_endpoint(
            stopendpoints.get_in_system_by_id,
            self.stopservice.get_in_system_by_id,
            (self.SYSTEM_ID, self.STOP_ID),
        )


class TestTripEndpoints(testutil.TestCase(tripendpoints), _TestEndpoints):
    def setUp(self):
        self.setUpSuper()
        self.tripservice = self.mockImportedModule(tripendpoints.tripservice)

    def test_list_all_in_route(self):
        """[Trip endpoints] List all trips in a route"""
        self._test_response_endpoint(
            tripendpoints.list_all_in_route,
            self.tripservice.list_all_in_route,
            (self.SYSTEM_ID, self.ROUTE_ID),
        )

    def test_get_in_route_by_id(self):
        """[Trip endpoints] Get a specific trip in a route"""
        self._test_response_endpoint(
            tripendpoints.get_in_route_by_id,
            self.tripservice.get_in_route_by_id,
            (self.SYSTEM_ID, self.ROUTE_ID, self.TRIP_ID),
        )


class TestSystemEndpoints(testutil.TestCase(systemendpoints), _TestEndpoints):
    def setUp(self):
        self.setUpSuper()
        self.flask = self.mockImportedModule(systemendpoints.flask)
        self.systemservice = self.mockImportedModule(systemendpoints.systemservice)

    def test_list_all(self):
        """[System endpoints] List all systems installed"""
        self._test_response_endpoint(
            systemendpoints.list_all, self.systemservice.list_all
        )

    def test_get_by_id(self):
        """[System endpoints] Get a specific system"""
        self._test_response_endpoint(
            systemendpoints.get_by_id, self.systemservice.get_by_id, self.SYSTEM_ID
        )

    def test_install(self):
        """[System endpoints] Install a system"""
        request = self.flask.request
        config_file_handle = mock.MagicMock()
        second_file = mock.MagicMock()
        request.files = {"config_file": config_file_handle, "second_file": second_file}
        request.form.to_dict.return_value = {"extra_setting": "value"}
        config_file_handle.read.return_value = b"ABCD"

        systemendpoints.install(self.SYSTEM_ID)

        self.systemservice.install.assert_called_once_with(
            system_id=self.SYSTEM_ID,
            config_str="ABCD",
            extra_files={"second_file": second_file.stream},
            extra_settings={"extra_setting": "value"},
        )

    def test_install__access_denied(self):
        """[System endpoints] Install a system - access denied"""
        self.ensure.side_effect = exceptions.AccessDenied
        self._test_access_denied(systemendpoints.install, self.SYSTEM_ID)

    def test_delete_by_id(self):
        """[System endpoints] Uninstall a system"""
        self._test_no_response_endpoint(
            systemendpoints.delete_by_id,
            self.systemservice.delete_by_id,
            self.SYSTEM_ID,
        )

    def test_delete_by_id__access_denied(self):
        """[System endpoints] Uninstall a system - access denied"""
        self.ensure.side_effect = exceptions.AccessDenied
        self._test_access_denied(systemendpoints.delete_by_id, self.SYSTEM_ID)


class TestFlaskApp(testutil.TestCase(flaskapp)):
    COMMIT_HASH = "b7e35a125f4c539c37deaf3a6ac72bd408097131"

    def test_root(self):
        """[Flask app] Test accessing root"""

        expected_code = 200

        (__, actual_code, __) = flaskapp.root()

        self.assertEqual(expected_code, actual_code)

    def test_404(self):
        """[Flask app] Test 404 error"""
        expected_code = 404

        (__, actual_code, __) = flaskapp.page_not_found(None)

        self.assertEqual(expected_code, actual_code)
