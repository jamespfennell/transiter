import unittest.mock as mock
import unittest

from transiter.endpoints import tripendpoints
from transiter.endpoints import systemendpoints
from transiter.endpoints import routeendpoints
from transiter.endpoints import stopendpoints
from transiter.endpoints import feedendpoints


class _TestEndpoints(unittest.TestCase):

    SYSTEM_ID = '1'
    ROUTE_ID = '2'
    TRIP_ID = '3'
    STOP_ID = '4'
    FEED_ID = '5'
    FEED_UPDATE_ID = '6'
    SERVICE_RESPONSE = {'A': 'B'}
    JSON_RESPONSE = 'C'
    SERVICE_NO_RESPONSE = True
    JSON_NO_RESPONSE = ''

    def setUp(self):
        patcher = mock.patch('transiter.endpoints.responsemanager.jsonutil')
        self.jsonutil = patcher.start()
        self.addCleanup(patcher.stop)

    def _test_endpoint(self, endpoint_function, service_function, args,
                       service_response, endpoint_response):

        service_function.return_value = service_response
        if endpoint_response != '':
            self.jsonutil.convert_for_http.return_value = endpoint_response

        (actual, __, __) = endpoint_function(*args)

        self.assertEqual(actual, endpoint_response)
        if endpoint_response != '':
            self.jsonutil.convert_for_http.assert_called_once_with(
                service_response)
        service_function.assert_called_once_with(*args)

    def _test_response_endpoint(self, endpoint_function, service_function, args=()):
        self._test_endpoint(endpoint_function, service_function, args,
                            self.SERVICE_RESPONSE, self.JSON_RESPONSE)

    def _test_no_response_endpoint(self, endpoint_function, service_function, args=()):
        self._test_endpoint(endpoint_function, service_function, args,
                            self.SERVICE_NO_RESPONSE, self.JSON_NO_RESPONSE)

    def _test_not_implemented_endpoint(self, endpoint_function, args=()):

        (actual, http_code, __) = endpoint_function(*args)

        self.assertEqual(actual, '')
        self.assertEqual(http_code, 501)


class TestFeedEndpoints(_TestEndpoints):

    @mock.patch('transiter.endpoints.feedendpoints.feedservice')
    def test_list_all_in_system(self, feedservice):
        self._test_response_endpoint(feedendpoints.list_all_in_system,
                                     feedservice.list_all_in_system,
                                     (self.SYSTEM_ID))

    @mock.patch('transiter.endpoints.feedendpoints.feedservice')
    def test_get_in_system_by_id(self, feedservice):
        self._test_response_endpoint(feedendpoints.get_in_system_by_id,
                                     feedservice.get_in_system_by_id,
                                     (self.SYSTEM_ID, self.ROUTE_ID))

    @mock.patch('transiter.endpoints.feedendpoints.feedservice')
    def test_create_feed_update(self, feedservice):
        self._test_response_endpoint(feedendpoints.create_feed_update,
                                     feedservice.create_feed_update,
                                     (self.SYSTEM_ID, self.FEED_ID))

    @mock.patch('transiter.endpoints.feedendpoints.feedservice')
    def test_list_updates_in_feed(self, feedservice):
        self._test_response_endpoint(feedendpoints.list_updates_in_feed,
                                     feedservice.list_updates_in_feed,
                                     (self.SYSTEM_ID, self.FEED_ID))

    @mock.patch('transiter.endpoints.feedendpoints.feedservice')
    def test_get_update_in_feed(self, feedservice):
        self._test_not_implemented_endpoint(feedendpoints.get_update_in_feed,
                                            (self.SYSTEM_ID, self.FEED_ID,
                                             self.FEED_UPDATE_ID))

    @mock.patch('transiter.endpoints.feedendpoints.feedservice')
    def test_get_autoupdater_for_feed(self, feedservice):
        self._test_not_implemented_endpoint(feedendpoints.get_autoupdater_for_feed,
                                            (self.SYSTEM_ID, self.FEED_ID))

    @mock.patch('transiter.endpoints.feedendpoints.feedservice')
    def test_configure_autoupdater_for_feed(self, feedservice):
        self._test_not_implemented_endpoint(
            feedendpoints.configure_autoupdater_for_feed,
                                     (self.SYSTEM_ID, self.FEED_ID))


class TestRouteEndpoints(_TestEndpoints):

    @mock.patch('transiter.endpoints.routeendpoints.routeservice')
    def test_list_all_in_system(self, routeservice):
        self._test_response_endpoint(routeendpoints.list_all_in_system,
                                     routeservice.list_all_in_system,
                                     (self.SYSTEM_ID))

    @mock.patch('transiter.endpoints.routeendpoints.routeservice')
    def test_get_in_system_by_id(self, routeservice):
        self._test_response_endpoint(routeendpoints.get_in_system_by_id,
                                     routeservice.get_in_system_by_id,
                                     (self.SYSTEM_ID, self.ROUTE_ID))


class TestStopEndpoints(_TestEndpoints):

    @mock.patch('transiter.endpoints.stopendpoints.stopservice')
    def test_list_all_in_route(self, stopservice):
        self._test_response_endpoint(stopendpoints.list_all_in_system,
                                     stopservice.list_all_in_system,
                                     (self.SYSTEM_ID))

    @mock.patch('transiter.endpoints.stopendpoints.stopservice')
    def test_get_in_route_by_id(self, stopservice):
        self._test_response_endpoint(stopendpoints.get_in_system_by_id,
                                     stopservice.get_in_system_by_id,
                                     (self.SYSTEM_ID, self.STOP_ID))


class TestTripEndpoints(_TestEndpoints):

    @mock.patch('transiter.endpoints.tripendpoints.tripservice')
    def test_list_all_in_route(self, tripservice):
        self._test_response_endpoint(tripendpoints.list_all_in_route,
                                     tripservice.list_all_in_route,
                                     (self.SYSTEM_ID, self.ROUTE_ID))

    @mock.patch('transiter.endpoints.tripendpoints.tripservice')
    def test_get_in_route_by_id(self, tripservice):
        self._test_response_endpoint(tripendpoints.get_in_route_by_id,
                                     tripservice.get_in_route_by_id,
                                     (self.SYSTEM_ID, self.ROUTE_ID, self.TRIP_ID))


class TestSystemEndpoints(_TestEndpoints):

    @mock.patch('transiter.endpoints.systemendpoints.systemservice')
    def test_list_all(self, systemservice):
        self._test_response_endpoint(systemendpoints.list_all,
                                     systemservice.list_all)

    @mock.patch('transiter.endpoints.systemendpoints.systemservice')
    def test_get_by_id(self, systemservice):
        self._test_response_endpoint(systemendpoints.get_by_id,
                                     systemservice.get_by_id,
                                     (self.SYSTEM_ID))

    @mock.patch('transiter.endpoints.systemendpoints.systemservice')
    def test_install(self, systemservice):
        self._test_no_response_endpoint(systemendpoints.install,
                                        systemservice.install,
                                        (self.SYSTEM_ID))

    @mock.patch('transiter.endpoints.systemendpoints.systemservice')
    def test_delete_by_id(self, systemservice):
        self._test_no_response_endpoint(systemendpoints.delete_by_id,
                                        systemservice.delete_by_id,
                                        (self.SYSTEM_ID))

