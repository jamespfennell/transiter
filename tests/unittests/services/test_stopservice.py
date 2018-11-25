import unittest
import unittest.mock as mock

import datetime
from transiter.services import stopservice
from transiter import models


class TestDirectionNamesMatcher(unittest.TestCase):

    STOP_PK = 1
    DIRECTION_NAME = 'Direction Name'

    def setUp(self):
        self.stop = models.Stop()
        self.stop.pk = self.STOP_PK

        self.stop_event = models.StopTimeUpdate()
        self.stop_event.track = None
        self.stop_event.stop_id_alias = None
        self.stop_event.trip = models.Trip()
        self.stop_event.trip.direction_id = None

        # Note: having the rule as a mock allows us to test interactions
        self.rule = models.DirectionNameRule()
        self.rule.stop_pk = self.STOP_PK
        self.rule.direction_id = None
        self.rule.track = None
        self.rule.stop_id_alias = None
        self.rule.name = self.DIRECTION_NAME

    def test_all_names(self):
        dnm = stopservice._DirectionNameMatcher([self.rule])

        self.assertEqual({self.DIRECTION_NAME}, dnm.all_names())

    def test_no_matching_stop_pk(self):
        self.rule.stop_pk = 2
        dnm = stopservice._DirectionNameMatcher([self.rule])

        direction_name = dnm.match(self.stop, self.stop_event)

        self.assertEqual(direction_name, None)

    def test_no_matching_direction_id(self):
        self.rule.direction_id = True
        dnm = stopservice._DirectionNameMatcher([self.rule])

        direction_name = dnm.match(self.stop, self.stop_event)

        self.assertEqual(direction_name, None)

    def test_no_matching_track(self):
        self.rule.track = 'Track'
        dnm = stopservice._DirectionNameMatcher([self.rule])

        direction_name = dnm.match(self.stop, self.stop_event)

        self.assertEqual(direction_name, None)

    def test_no_matching_stop_id_alias(self):
        self.rule.stop_id_alias = 'StopIdAlias'
        dnm = stopservice._DirectionNameMatcher([self.rule])

        direction_name = dnm.match(self.stop, self.stop_event)

        self.assertEqual(direction_name, None)

    def test_match(self):
        dnm = stopservice._DirectionNameMatcher([self.rule])

        direction_name = dnm.match(self.stop, self.stop_event)

        self.assertEqual(direction_name, self.DIRECTION_NAME)


class TestStopEventFilter(unittest.TestCase):

    DIRECTION_NAME = '1'
    DATETIME_ONE = datetime.datetime(2000, 1, 1, 1, 0, 0)
    DATETIME_TWO = datetime.datetime(2000, 1, 1, 2, 0, 0)
    ROUTE_ID = '1'

    def setUp(self):

        self.stop_event_filter = stopservice._StopEventFilter()
        self.stop_event = models.StopTimeUpdate()
        self.stop_event.arrival_time = self.DATETIME_ONE
        self.stop_event.trip = models.Trip()
        self.stop_event.trip.route = models.Route()
        self.stop_event.trip.route_id = self.ROUTE_ID

    def test_add_direction_name(self):
        self.stop_event_filter._add_direction_name(self.DIRECTION_NAME)

        self.assertDictEqual(
            self.stop_event_filter._count,
            {self.DIRECTION_NAME: 0}
        )
        self.assertDictEqual(
            self.stop_event_filter._route_ids_so_far,
            {self.DIRECTION_NAME: set()}
        )

    def test_add_direction_name_already_added(self):
        self.stop_event_filter._count[self.DIRECTION_NAME] = 50
        self.stop_event_filter._add_direction_name(self.DIRECTION_NAME)

        self.assertDictEqual(
            self.stop_event_filter._count,
            {self.DIRECTION_NAME: 50}
        )

    @mock.patch('transiter.services.stopservice.time')
    def test_exclude_time_passed(self, time):
        self.stop_event_filter._add_direction_name(self.DIRECTION_NAME)
        time.time.return_value = self.DATETIME_TWO.timestamp()

        exclude = self.stop_event_filter.exclude(
            self.stop_event, self.DIRECTION_NAME)

        self.assertTrue(exclude)

    @mock.patch('transiter.services.stopservice.time')
    def test_exclude_route_not_there_yet(self, time):
        self.stop_event_filter._add_direction_name(self.DIRECTION_NAME)
        self.stop_event_filter._count[self.DIRECTION_NAME] = 100
        time.time.return_value = self.DATETIME_ONE.timestamp()
        self.stop_event.departure_time = self.DATETIME_ONE

        exclude = self.stop_event_filter.exclude(
            self.stop_event, self.DIRECTION_NAME)

        self.assertFalse(exclude)


class TestStopService(unittest.TestCase):

    SYSTEM_ID = '1'
    STOP_ONE_ID = '2'
    STOP_ONE_PK = 3
    STOP_ONE_REPR = {'stop_id': STOP_ONE_ID}
    ALL_DIRECTION_NAMES = ['A', 'B']
    STOP_ONE_HREF = '10'
    TRIP_HREF = '11'
    ROUTE_HREF = '12'
    TRIP_REPR = {'21': '22'}
    ROUTE_REPR = {'23': '24'}
    STOP_EVENT_REPR = {'25': '26'}
    DEFAULT_TRIPS = ['31', '32', '33']

    def _quick_mock(self, name):
        cache_name = '_quick_mock_cache_{}'.format(name)
        self.__setattr__(cache_name, mock.patch(
            'transiter.services.stopservice.{}'.format(name)))
        mocked = getattr(self, cache_name).start()
        self.addCleanup(getattr(self, cache_name).stop)
        return mocked

    def setUp(self):
        self.linksutil = self._quick_mock('linksutil')
        self.stop_dao = self._quick_mock('stop_dao')

        self.stop_one = mock.MagicMock()
        self.stop_one.pk = self.STOP_ONE_PK
        self.stop_one.id = self.STOP_ONE_ID
        self.stop_one.short_repr.return_value = self.STOP_ONE_REPR
        self.stop_dao.list_all_in_system.return_value = [
            self.stop_one]

        self.linksutil.StopEntityLink.return_value = self.STOP_ONE_HREF
        self.linksutil.RouteEntityLink.return_value = self.ROUTE_HREF
        self.linksutil.TripEntityLink.return_value = self.TRIP_HREF

    def test_list_all_in_system(self):
        expected = [
            {
                'href': self.STOP_ONE_HREF,
                **self.STOP_ONE_REPR
            }
        ]

        actual = stopservice.list_all_in_system(self.SYSTEM_ID)

        self.assertListEqual(actual, expected)
        self.stop_one.short_repr.assert_called_once_with()
        self.linksutil.StopEntityLink.assert_called_once_with(self.stop_one)
        self.stop_dao.list_all_in_system.assert_called_once_with(self.SYSTEM_ID)

    @mock.patch('transiter.services.stopservice.service_pattern_dao')
    @mock.patch('transiter.services.stopservice.stop_event_dao')
    @mock.patch('transiter.services.stopservice._StopEventFilter')
    @mock.patch('transiter.services.stopservice._DirectionNameMatcher')
    def test_get_in_system_by_id(self, _DirectionNameMatcher, _StopEventFilter,
                                 stop_event_dao, service_pattern_dao):

        self.stop_one.parent_stop = None
        self.stop_one.child_stops = []
        self.stop_dao.get_in_system_by_id.return_value = self.stop_one
        service_pattern_dao.get_default_trips_at_stops.return_value = {
            self.STOP_ONE_PK: self.DEFAULT_TRIPS
        }

        stop_event_one = mock.MagicMock()
        stop_event_two = mock.MagicMock()
        stop_event_two.stop = self.stop_one
        stop_event_two.short_repr.return_value = self.STOP_EVENT_REPR
        stop_event_two.trip.long_repr.return_value = self.TRIP_REPR
        stop_event_two.trip.route.short_repr.return_value = self.ROUTE_REPR
        stop_event_dao.get_by_stop_pks.return_value = [stop_event_one, stop_event_two]

        direction_name_matcher = mock.MagicMock()
        _DirectionNameMatcher.return_value = direction_name_matcher
        direction_name_matcher.all_names.return_value = self.ALL_DIRECTION_NAMES
        direction_name_matcher.match.side_effect = self.ALL_DIRECTION_NAMES

        stop_event_filter = mock.MagicMock()
        _StopEventFilter.return_value = stop_event_filter
        stop_event_filter.exclude.side_effect = [True, False]

        expected_response = {
            **self.STOP_ONE_REPR,
            'usual_routes': self.DEFAULT_TRIPS,
            'direction_names': self.ALL_DIRECTION_NAMES,
            'stop_events': [
                {
                    'direction_name': self.ALL_DIRECTION_NAMES[1],
                    'stop_id': self.STOP_ONE_ID,
                    **self.STOP_EVENT_REPR,
                    'trip': {
                        **self.TRIP_REPR,
                        'route': {
                            **self.ROUTE_REPR,
                            'href': self.ROUTE_HREF
                        },
                        'href': self.TRIP_HREF
                    }
                }
            ],
            'child_stops': [],
            'parent_stop': None
        }


        actual_response = stopservice.get_in_system_by_id(self.SYSTEM_ID, self.STOP_ONE_ID)

        print(expected_response)
        print(actual_response)
        self.assertDictEqual(expected_response, actual_response)
