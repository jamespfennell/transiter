import unittest.mock as mock
import unittest

from transiter.endpoints import tripendpoints
from transiter.endpoints import systemendpoints


class TestEndpoints(unittest.TestCase):

    SYSTEM_ID = '1'
    ROUTE_ID = '2'
    TRIP_ID = '3'
    SERVICE_RESPONSE = {'A': 'B'}
    JSON_RESPONSE = 'C'

    def setUp(self):
        patcher = mock.patch('transiter.endpoints.responsemanager.jsonutil')
        self.jsonutil = patcher.start()
        self.addCleanup(patcher.stop)

    def _test_endpoint_routing(self, endpoint_function, service_function, args=()):

        service_function.return_value = self.SERVICE_RESPONSE
        self.jsonutil.convert_for_http.return_value = self.JSON_RESPONSE

        (actual, __, __) = endpoint_function(*args)

        self.assertEqual(actual, self.JSON_RESPONSE)
        self.jsonutil.convert_for_http.assert_called_once_with(
            self.SERVICE_RESPONSE)
        service_function.assert_called_once_with(*args)

    @mock.patch('transiter.endpoints.tripendpoints.tripservice')
    def test_trip_service_list_all_in_route(self, tripservice):
        self._test_endpoint_routing(tripendpoints.list_all_in_route,
                                    tripservice.list_all_in_route,
                                    (self.SYSTEM_ID, self.ROUTE_ID))

    @mock.patch('transiter.endpoints.tripendpoints.tripservice')
    def test_trip_service_get_in_route_by_id(self, tripservice):
        self._test_endpoint_routing(tripendpoints.get_in_route_by_id,
                                    tripservice.get_in_route_by_id,
                                    (self.SYSTEM_ID, self.ROUTE_ID, self.TRIP_ID))


    @mock.patch('transiter.endpoints.systemendpoints.systemservice')
    def test_system_service_list_all(self, systemservice):
        self._test_endpoint_routing(systemendpoints.list_all,
                                    systemservice.list_all)


