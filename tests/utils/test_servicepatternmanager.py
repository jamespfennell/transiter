import unittest
from unittest import mock
from transiter.utils import servicepatternmanager
from transiter.utils import gtfsstaticutil


class TestTripsFilter(unittest.TestCase):
    @mock.patch('transiter.utils.servicepatternmanager._TripMatcher')
    def test_filter_trips_by_conditions(self, _TripMatcher):
        trip_matcher = mock.MagicMock()
        _TripMatcher.return_value = trip_matcher
        trip_matcher.match.side_effect = self._dummy_match

        good_trips = [self._create_trip(0) for __ in range(10)]
        bad_trips = [self._create_trip(20) for __ in range(10)]
        ugly_trips = [self._create_trip(7) for __ in range(1)]

        actual_trips = servicepatternmanager._filter_trips_by_conditions(
            good_trips + bad_trips + ugly_trips, 0.2, None
        )

        self.assertListEqual(actual_trips, [good_trips[0]])

    @staticmethod
    def _dummy_match(trip):
        return trip.stop_ids[0] < 10

    @staticmethod
    def _create_trip(key):
        trip = mock.MagicMock()
        trip.stop_ids = [key, 100]
        return trip


class TestTripMatcher(unittest.TestCase):

    def setUp(self):
        self.early_weekday_trip = self._create_trip({
            'start_time': 6,
            'end_time': 8,
            'monday': True
        })

        self.mid_weekday_trip = self._create_trip({
            'start_time': 12,
            'end_time': 14,
            'tuesday': True
        })

        self.late_weekday_trip = self._create_trip({
            'start_time': 22,
            'end_time': 23,
            'wednesday': True
        })

        self.early_weekend_trip = self._create_trip({
            'start_time': 6,
            'end_time': 8,
            'sunday': True
        })

        self.trips = [
            self.early_weekday_trip,
            self.mid_weekday_trip,
            self.late_weekday_trip,
            self.early_weekend_trip]

    def test_one(self):
        raw_conds = {
            "weekday": True,
            "one_of": {
                "starts_earlier_than": 7,
                "starts_later_than": 20
            }
        }
        expected_trips = [self.early_weekday_trip, self.late_weekday_trip]

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    def test_two(self):
        raw_conds = {
            "all_of": {
                "starts_earlier_than": 7,
                "starts_later_than": 7.01
            }
        }
        expected_trips = []

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    def test_three(self):
        raw_conds = {
            "weekday": True,
            "starts_later_than": 7,
            "starts_earlier_than": 20
        }
        expected_trips = [self.mid_weekday_trip]

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    def test_four(self):
        raw_conds = {
            "none_of": {
                "ends_later_than": 13,
            }
        }
        expected_trips = [self.early_weekday_trip, self.early_weekend_trip]

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    @staticmethod
    def _trip_matcher_runner(raw_conds, trips):
        trips_matcher = servicepatternmanager._TripMatcher(raw_conds)
        matched_trips = []
        for trip in trips:
            if trips_matcher.match(trip):
                matched_trips.append(trip)
        return matched_trips

    @staticmethod
    def _create_trip(attrs):
        trip = gtfsstaticutil.StaticTrip()
        for day in gtfsstaticutil.days:
            trip.__setattr__(day, False)
        for key, value in attrs.items():
            trip.__setattr__(key, value)
        return trip

