import unittest.mock as mock
import unittest

from transiter.endpoints import tripendpoints


class TestTripEndpoints(unittest.TestCase):

    SYSTEM_ID = '1'
    ROUTE_ID = '2'
    TRIP_ONE_ID = '3'
    TRIP_ONE_REPR = {'trip_id': TRIP_ONE_ID}
    TRIP_TWO_REPR = {'trip_id': '4'}
    STOP_REPR = {'stop_id': '5'}
    STOP_EVENT_REPR = {'track': 'Track Two'}

    @classmethod
    def setUp(cls):
        cls.trip_one = mock.MagicMock()
        cls.trip_one.repr_for_list.return_value = cls.TRIP_ONE_REPR
        cls.trip_one.repr_for_get.return_value = cls.TRIP_ONE_REPR

        cls.trip_two = mock.MagicMock()
        cls.trip_two.repr_for_list.return_value = cls.TRIP_TWO_REPR

        stop = mock.MagicMock()
        stop.repr_for_list.return_value = cls.STOP_REPR

        stop_event = mock.MagicMock()
        stop_event.repr_for_list.return_value = cls.STOP_EVENT_REPR
        stop_event.stop = stop
        cls.trip_one.stop_events = [stop_event]

    @mock.patch('transiter.endpoints.tripendpoints.tripservice')
    def test_list_all_in_route(self, tripservice):
        #trip_endpoints.route.return_value = lambda x: '3'
        #http_get_response.return_value = lambda x: '2'
        tripservice.list_all_in_route.return_value = '1'

        a = tripendpoints.list_all_in_route(self.SYSTEM_ID,
                                        self.ROUTE_ID)
        print('Hello')
        print(a)




