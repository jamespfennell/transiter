import unittest
from unittest import mock
from transiter.utils import servicepatternmanager
from transiter.utils import gtfsstaticutil

import itertools


class TestServicePatternManager(unittest.TestCase):
    @mock.patch('transiter.utils.servicepatternmanager.graphutils')
    def test_path_lists_to_sorted_graph__empty_list(self, graphutils):
        """[Service pattern manager] Empty path list to sorted graph"""
        graph = mock.MagicMock()
        graphutils.graphdatastructs.DirectedPath.return_value = graph

        actual = servicepatternmanager._path_lists_to_sorted_graph([])

        self.assertEqual(graph, actual)

        graphutils.graphdatastructs.DirectedPath.assert_called_once_with([])

    @mock.patch('transiter.utils.servicepatternmanager.graphutils')
    def test_path_lists_to_sorted_graph__single_list(self, graphutils):
        """[Service pattern manager] Single path list to sorted graph"""
        path_list = mock.MagicMock()
        path_lists = [path_list]
        graph = mock.MagicMock()
        graphutils.graphdatastructs.DirectedPath.return_value = graph

        actual = servicepatternmanager._path_lists_to_sorted_graph(path_lists)

        self.assertEqual(graph, actual)

        graphutils.graphdatastructs.DirectedPath.assert_called_once_with(path_list)


    @mock.patch('transiter.utils.servicepatternmanager.graphutils')
    def test_path_lists_to_sorted_graph__stiches_to_path(self, graphutils):
        """[Service pattern manager] Two path lists to sorted graph, just from stitching"""
        path_list_one = mock.MagicMock()
        path_list_two = mock.MagicMock()
        path_lists = [path_list_one, path_list_two]

        directed_path_one = mock.MagicMock()
        directed_path_two = mock.MagicMock()

        def DirectedPath(path_list):
            if path_list == path_list_one:
                return directed_path_one
            if path_list == path_list_two:
                return directed_path_two
            raise AttributeError

        graphutils.graphdatastructs.DirectedPath.side_effect = DirectedPath

        graph = mock.MagicMock()
        graphutils.pathstitcher.stitch.return_value = graph
        graph.is_path.return_value = True
        final_graph = mock.MagicMock()
        graph.cast_to_path.return_value = final_graph

        actual = servicepatternmanager._path_lists_to_sorted_graph(path_lists)

        self.assertEqual(final_graph, actual)

        graphutils.graphdatastructs.DirectedPath.assert_any_call(path_list_two)
        graphutils.graphdatastructs.DirectedPath.assert_any_call(path_list_one)
        graphutils.pathstitcher.stitch.assert_called_once_with([directed_path_one, directed_path_two])
        graph.is_path.assert_called_once_with()
        graph.cast_to_path.assert_called_once_with()
        graphutils.topologicalsort.sort.assert_not_called()


    @mock.patch('transiter.utils.servicepatternmanager.graphutils')
    def test_path_lists_to_sorted_graph__topological_sort(self, graphutils):
        """[Service pattern manager] Two path lists to sorted graph, from top sort"""
        path_list_one = mock.MagicMock()
        path_list_two = mock.MagicMock()
        path_lists = [path_list_one, path_list_two]

        directed_path_one = mock.MagicMock()
        directed_path_two = mock.MagicMock()

        def DirectedPath(path_list):
            if path_list == path_list_one:
                return directed_path_one
            if path_list == path_list_two:
                return directed_path_two
            raise AttributeError

        graphutils.graphdatastructs.DirectedPath.side_effect = DirectedPath

        graph = mock.MagicMock()
        graphutils.pathstitcher.stitch.return_value = graph
        graph.is_path.return_value = False
        final_graph = mock.MagicMock()
        graphutils.topologicalsort.sort.return_value = final_graph

        actual = servicepatternmanager._path_lists_to_sorted_graph(path_lists)

        self.assertEqual(final_graph, actual)

        graphutils.graphdatastructs.DirectedPath.assert_any_call(path_list_two)
        graphutils.graphdatastructs.DirectedPath.assert_any_call(path_list_one)
        graphutils.pathstitcher.stitch.assert_called_once_with([directed_path_one, directed_path_two])
        graph.is_path.assert_called_once_with()
        graph.cast_to_path.assert_not_called()
        graphutils.topologicalsort.sort.assert_called_with(graph)



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

        self.assertListEqual(actual_trips, good_trips)

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

