import unittest.mock as mock
import unittest

from transiter.endpoints import tripendpoints


class TestTripEndpoints(unittest.TestCase):

    SYSTEM_ID = '1'
    ROUTE_ID = '2'
    TRIP_ID = '3'
    SERVICE_RESPONSE = {'A': 'B'}
    JSON_RESPONSE = 'C'

    @mock.patch('transiter.endpoints.responsemanager.jsonutil')
    @mock.patch('transiter.endpoints.tripendpoints.tripservice')
    def test_list_all_in_route(self,
                               tripservice,
                               jsonutil):
        tripservice.list_all_in_route.return_value = self.SERVICE_RESPONSE
        jsonutil.convert_for_http.return_value = self.JSON_RESPONSE

        (actual, __, __) = tripendpoints.list_all_in_route(self.SYSTEM_ID,
                                                           self.ROUTE_ID)

        self.assertEqual(actual, self.JSON_RESPONSE)
        jsonutil.convert_for_http.assert_called_once_with(self.SERVICE_RESPONSE)
        tripservice.list_all_in_route.assert_called_once_with(self.SYSTEM_ID,
                                                              self.ROUTE_ID)

    @mock.patch('transiter.endpoints.responsemanager.jsonutil')
    @mock.patch('transiter.endpoints.tripendpoints.tripservice')
    def test_get_in_route_by_id(self,
                                tripservice,
                                jsonutil):
        tripservice.get_in_route_by_id.return_value = self.SERVICE_RESPONSE
        jsonutil.convert_for_http.return_value = self.JSON_RESPONSE

        (actual, __, __) = tripendpoints.get_in_route_by_id(self.SYSTEM_ID,
                                                            self.ROUTE_ID,
                                                            self.TRIP_ID)

        self.assertEqual(actual, self.JSON_RESPONSE)
        jsonutil.convert_for_http.assert_called_once_with(self.SERVICE_RESPONSE)
        tripservice.get_in_route_by_id.assert_called_once_with(self.SYSTEM_ID,
                                                               self.ROUTE_ID,
                                                               self.TRIP_ID)
