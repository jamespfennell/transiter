import unittest.mock as mock
import unittest
from transiter.services import tripservice

SYSTEM_ID = '1'
ROUTE_ID = '2'
TRIP_ONE_ID = '3'

TRIP_ONE_REPR = {'trip_id': TRIP_ONE_ID}
TRIP_TWO_REPR = {'trip_id': '4'}

trip_one = mock.MagicMock()
trip_one.repr_for_list.return_value = TRIP_ONE_REPR
trip_one.repr_for_get.return_value = TRIP_ONE_REPR

trip_two = mock.MagicMock()
trip_two.repr_for_list.return_value = TRIP_TWO_REPR


STOP_ONE_REPR = {'stop_id': '5'}


stop_one = mock.MagicMock()
stop_one.repr_for_list.return_value = STOP_ONE_REPR

STOP_EVENT_ONE_REPR = {'track': 'Track Two'}

stop_event_one = mock.MagicMock()
stop_event_one.repr_for_list.return_value = STOP_EVENT_ONE_REPR
stop_event_one.stop = stop_one
trip_one.stop_events = [stop_event_one]

class TestTripService(unittest.TestCase):

    @mock.patch('transiter.services.tripservice.trip_dao')
    def test_list_all_in_route(self, trip_dao):
        expected = [TRIP_ONE_REPR, TRIP_TWO_REPR]
        trip_dao.list_all_in_route.return_value = [trip_one, trip_two]

        actual = tripservice.list_all_in_route(SYSTEM_ID, ROUTE_ID)

        self.assertEqual(actual, expected)
        trip_dao.list_all_in_route.assert_called_once_with(SYSTEM_ID, ROUTE_ID)
        trip_one.repr_for_list.assert_called_once()
        trip_two.repr_for_list.assert_called_once()
        pass


    @mock.patch('transiter.services.tripservice.trip_dao')
    def test_get_in_route_by_id(self, trip_dao):
        expected = dict({
            'stop_events': [
                dict({
                    'stop': STOP_ONE_REPR
                }, **STOP_EVENT_ONE_REPR)
            ]
        }, **TRIP_ONE_REPR)
        trip_dao.get_in_route_by_id.return_value = trip_one

        actual = tripservice.get_in_route_by_id(SYSTEM_ID, ROUTE_ID, TRIP_ONE_ID)


        self.assertDictEqual(actual, expected)

