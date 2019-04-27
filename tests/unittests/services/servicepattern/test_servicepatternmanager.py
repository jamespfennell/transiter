import datetime
import unittest
from unittest import mock

from transiter import models
from transiter.services.servicepattern import servicepatternmanager
from transiter.services.update import gtfsstaticutil


class TestServicePatternManager(unittest.TestCase):
    def setUp(self):

        self.trip_one = models.ScheduledTrip()
        self.trip_one.stop_ids = []
        self.trip_one.route_id = 'C'
        self.trip_two = models.ScheduledTrip()
        self.trip_two.stop_ids = ['1', '2']
        self.trip_two.route_id = 'A'
        self.trip_two.direction_id = False
        self.trip_three = models.ScheduledTrip()
        self.trip_three.stop_ids = ['3', '4']
        self.trip_three.route_id = 'A'
        self.trip_three.direction_id = True

    @mock.patch('transiter.services.servicepattern.servicepatternmanager.graphutils')
    def test_path_lists_to_sorted_graph__empty_list(self, graphutils):
        """[Service pattern manager] Empty path list to sorted graph"""
        graph = mock.MagicMock()
        graphutils.graphdatastructs.DirectedPath.return_value = graph

        actual = servicepatternmanager._paths_to_sorted_graph([])

        self.assertEqual(graph, actual)

        graphutils.graphdatastructs.DirectedPath.assert_called_once_with([])

    @mock.patch('transiter.services.servicepattern.servicepatternmanager.graphutils')
    def test_path_lists_to_sorted_graph__single_list(self, graphutils):
        """[Service pattern manager] Single path list to sorted graph"""
        path_list = mock.MagicMock()
        path_lists = [path_list]
        graph = mock.MagicMock()
        graphutils.graphdatastructs.DirectedPath.return_value = graph

        actual = servicepatternmanager._paths_to_sorted_graph(path_lists)

        self.assertEqual(graph, actual)

        graphutils.graphdatastructs.DirectedPath.assert_called_once_with(path_list)

    def test_sorted_graph_to_service_pattern(self):
        """[Service pattern manager] Sorted graph to service pattern"""
        label_one = '1'
        label_two = '2'
        path_list = [label_one, label_two]
        graph = servicepatternmanager.graphutils.graphdatastructs.DirectedPath(path_list)

        stop_one = mock.MagicMock()
        stop_two = mock.MagicMock()
        label_to_stop = {
            label_one: stop_one,
            label_two: stop_two
        }

        expected_sp = models.ServicePattern()
        v_one = models.ServicePatternVertex()
        v_one.stop_pk = label_one
        v_one.service_pattern = expected_sp
        v_one.position = 0
        v_two = models.ServicePatternVertex()
        v_two.stop_pk = label_two
        v_two.service_pattern = expected_sp
        v_two.position = 1

        actual_sp = servicepatternmanager._sorted_graph_to_service_pattern(
            graph)

        self.assertEqual(expected_sp, actual_sp)
        self.assertEqual(expected_sp.vertices, actual_sp.vertices)

    @mock.patch('transiter.services.servicepattern.servicepatternmanager.graphutils')
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

        actual = servicepatternmanager._paths_to_sorted_graph(path_lists)

        self.assertEqual(final_graph, actual)

        graphutils.graphdatastructs.DirectedPath.assert_any_call(path_list_two)
        graphutils.graphdatastructs.DirectedPath.assert_any_call(path_list_one)
        graphutils.pathstitcher.stitch.assert_called_once_with([directed_path_one, directed_path_two])
        graph.is_path.assert_called_once_with()
        graph.cast_to_path.assert_called_once_with()
        graphutils.topologicalsort.sort.assert_not_called()

    @mock.patch('transiter.services.servicepattern.servicepatternmanager.graphutils')
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

        actual = servicepatternmanager._paths_to_sorted_graph(path_lists)

        self.assertEqual(final_graph, actual)

        graphutils.graphdatastructs.DirectedPath.assert_any_call(path_list_two)
        graphutils.graphdatastructs.DirectedPath.assert_any_call(path_list_one)
        graphutils.pathstitcher.stitch.assert_called_once_with([directed_path_one, directed_path_two])
        graph.is_path.assert_called_once_with()
        graph.cast_to_path.assert_not_called()
        graphutils.topologicalsort.sort.assert_called_with(graph)




class TestTripMatcher(unittest.TestCase):
    DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    def setUp(self):
        self.early_weekday_trip = self._create_trip({
            'start_time': datetime.time(hour=6, minute=0, second=0),
            'end_time': datetime.time(hour=8, minute=0, second=0),
            'monday': True,
            'route_id': 'A'
        })

        self.mid_weekday_trip = self._create_trip({
            'start_time': datetime.time(hour=12, minute=0, second=0),
            'end_time': datetime.time(hour=14, minute=0, second=0),
            'tuesday': True,
            'route_id': 'A'
        })

        self.late_weekday_trip = self._create_trip({
            'start_time': datetime.time(hour=22, minute=0, second=0),
            'end_time': datetime.time(hour=23, minute=0, second=0),
            'wednesday': True,
            'route_id': 'B'
        })

        self.early_weekend_trip = self._create_trip({
            'start_time': datetime.time(hour=6, minute=0, second=0),
            'end_time': datetime.time(hour=8, minute=0, second=0),
            'sunday': True,
            'route_id': 'C'
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

    def test_five(self):
        raw_conds = {
            "all_of": {
                "ends_earlier_than": 11,
                "weekday": True,
            }
        }
        expected_trips = [self.early_weekday_trip]

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    def test_six(self):
        raw_conds = {
            "weekend": True
        }
        expected_trips = [self.early_weekend_trip]

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    def _test_seven(self):
        raw_conds = {
            'route_id': 'A'
        }
        expected_trips = [self.early_weekday_trip, self.mid_weekday_trip]

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    def _test_eight(self):
        raw_conds = {
            'route_id': ['B', 'C']
        }
        expected_trips = [self.late_weekday_trip, self.early_weekend_trip]

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    def test_nine(self):
        raw_conds = {
            'unknown_condition': True
        }

        self.assertRaises(
            NotImplementedError,
            self._trip_matcher_runner,
            raw_conds,
            self.trips)

    @staticmethod
    def _trip_matcher_runner(raw_conds, trips):
        trips_matcher = servicepatternmanager._ScheduledTripMatcher(raw_conds)
        matched_trips = []
        for trip in trips:
            if trips_matcher.match(trip):
                matched_trips.append(trip)
        return matched_trips

    def _create_trip(self, attrs):
        trip = models.ScheduledTrip()
        service = models.ScheduledService()
        trip.service = service
        for day in self.DAYS:
            service.__setattr__(day, False)
        days = set(self.DAYS)
        for key, value in attrs.items():
            if key in days:
                service.__setattr__(key, value)
            else:
                trip.__setattr__(key, value)
        return trip
