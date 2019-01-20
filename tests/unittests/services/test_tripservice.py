import unittest.mock as mock
import unittest
from transiter.services import tripservice


class TestTripService(unittest.TestCase):

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
        cls.trip_one.pk = 5
        cls.trip_one.short_repr.return_value = cls.TRIP_ONE_REPR
        cls.trip_one.long_repr.return_value = cls.TRIP_ONE_REPR

        cls.trip_two = mock.MagicMock()
        cls.trip_two.pk = 6
        cls.trip_two.short_repr.return_value = cls.TRIP_TWO_REPR

        stop = mock.MagicMock()
        stop.short_repr.return_value = cls.STOP_REPR

        stop_event = mock.MagicMock()
        stop_event.short_repr.return_value = cls.STOP_EVENT_REPR
        stop_event.stop = stop
        stop_event.future = True
        cls.trip_one.stop_events = [stop_event]

    # TODO: renable these tests or are they pointless?
    '''
    @mock.patch('transiter.services.tripservice.tripdam')
    def test_list_all_in_route(self, trip_dao):
        """[Trip service] List all trips in a route"""
        expected = [self.TRIP_ONE_REPR, self.TRIP_TWO_REPR]
        trip_dao.list_all_in_route.return_value = [self.trip_one,
                                                   self.trip_two]
        trip_dao.get_trip_pk_to_last_stop_map.return_value = {
            5: mock.MagicMock(),
            6: mock.MagicMock(),
        }

        actual = tripservice.list_all_in_route(self.SYSTEM_ID, self.ROUTE_ID)
        for trip in actual:
            del trip['last_stop']

        self.assertEqual(actual, expected)
        trip_dao.list_all_in_route.assert_called_once_with(self.SYSTEM_ID,
                                                           self.ROUTE_ID)
        self.trip_one.short_repr.assert_called_once()
        self.trip_two.short_repr.assert_called_once()
        pass

    @mock.patch('transiter.services.tripservice.tripdam')
    def test_get_in_route_by_id(self, trip_dao):
        """[Trip service] Get a specific trip in a route"""
        expected = {
            'stop_events': [{
                'stop': self.STOP_REPR,
                'future': True,
                **self.STOP_EVENT_REPR
            }],
            **self.TRIP_ONE_REPR
        }
        trip_dao.get_in_route_by_id.return_value = self.trip_one

        actual = tripservice.get_in_route_by_id(self.SYSTEM_ID,
                                                self.ROUTE_ID,
                                                self.TRIP_ONE_ID)

        self.assertDictEqual(actual, expected)
        trip_dao.get_in_route_by_id.assert_called_once_with(self.SYSTEM_ID,
                                                            self.ROUTE_ID,
                                                            self.TRIP_ONE_ID)
    '''



