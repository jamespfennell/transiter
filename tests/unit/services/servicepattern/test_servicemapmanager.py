import datetime
import unittest
from unittest import mock

from transiter import models
from transiter.services.servicemap import servicemapmanager
from ... import testutil


class TestServiceMapManager(testutil.TestCase(servicemapmanager)):
    STOP_1_PK = 1
    GROUP_ID = "2"
    ROUTE_1_ID = "3"
    ROUTE_1_PK = 6
    ROUTE_2_ID = "4"
    ROUTE_2_PK = 7
    TRIP_1_PK = 10
    TRIP_2_PK = 11
    TRIP_1_START_TIME = datetime.datetime(1, 5, 9)
    TRIP_1_END_TIME = datetime.datetime(2, 6, 10)
    TRIP_2_START_TIME = datetime.datetime(3, 7, 11)
    TRIP_2_END_TIME = datetime.datetime(4, 8, 12)

    def setUp(self):

        self.actual_graphutils = servicemapmanager.graphutils
        self.graphutils = self.mockImportedModule(servicemapmanager.graphutils)
        self.servicemapdam = self.mockImportedModule(servicemapmanager.servicemapdam)
        self.scheduledam = self.mockImportedModule(servicemapmanager.scheduledam)
        self.stopdam = self.mockImportedModule(servicemapmanager.stopdam)
        self.tripdam = self.mockImportedModule(servicemapmanager.tripdam)

        self.trip_one = models.ScheduledTrip(pk=self.TRIP_1_PK)
        self.trip_one.stop_ids = []
        self.trip_one.route_id = "C"
        self.trip_one.direction_id = True
        self.trip_two = models.ScheduledTrip(pk=self.TRIP_2_PK)
        self.trip_two.stop_ids = ["1", "2"]
        self.trip_two.route_id = "A"
        self.trip_two.direction_id = False
        self.trip_three = models.ScheduledTrip()
        self.trip_three.stop_ids = ["3", "4"]
        self.trip_three.route_id = "A"
        self.trip_three.direction_id = True

        self.system = models.System()
        self.route_1 = models.Route(
            pk=self.ROUTE_1_PK, id=self.ROUTE_1_ID, system=self.system
        )
        self.route_2 = models.Route(
            pk=self.ROUTE_2_PK, id=self.ROUTE_2_ID, system=self.system
        )

        self.service_map_group_realtime = models.ServiceMapGroup(
            source=models.ServiceMapGroup.ServiceMapSource.REALTIME
        )
        self.service_map_realtime_1 = models.ServiceMap(
            group=self.service_map_group_realtime, route_pk=self.ROUTE_1_PK
        )
        self.service_map_realtime_2 = models.ServiceMap(
            group=self.service_map_group_realtime, route=self.route_2
        )
        self.service_map_group_schedule = models.ServiceMapGroup(
            source=models.ServiceMapGroup.ServiceMapSource.SCHEDULE,
            conditions='{"weekday": true}',
            threshold=0,
        )
        self.service_map_schedule_1 = models.ServiceMap(
            group=self.service_map_group_schedule, route=self.route_1
        )
        self.service_map_schedule_2 = models.ServiceMap(
            group=self.service_map_group_schedule, route=self.route_2
        )
        self.system.service_map_groups = [
            self.service_map_group_schedule,
            self.service_map_group_realtime,
        ]

    @mock.patch.object(servicemapmanager, "_build_service_map_from_paths")
    def test_calculate_realtime_service_map_for_route(
        self, _build_service_map_from_paths
    ):
        """[Service map manager] Calculate realtime service map for route"""

        self.route_1.trips = [self.trip_one, self.trip_two]

        self.tripdam.get_trip_pk_to_path_map.return_value = {
            self.TRIP_1_PK: [1, 2, 3, 4],
            self.TRIP_2_PK: [3, 1, 0],
        }
        self.stopdam.get_stop_pk_to_station_pk_map_in_system.return_value = {
            0: 0,
            1: 11,
            2: 2,
            3: 3,
            4: 14,
        }

        new_service_map = models.ServiceMap()
        _build_service_map_from_paths.return_value = new_service_map

        expected_paths = {(11, 2, 3, 14), (0, 11, 3)}

        servicemapmanager.calculate_realtime_service_map_for_route(self.route_1)

        _build_service_map_from_paths.assert_called_once_with(expected_paths)
        self.assertEqual(new_service_map.route, self.route_1)
        self.assertEqual(new_service_map.group, self.service_map_group_realtime)
        self.assertEqual(None, self.service_map_realtime_1.group)

    @mock.patch.object(servicemapmanager, "_ScheduledTripMatcher")
    @mock.patch.object(servicemapmanager, "_build_service_map_from_paths")
    def test_calculate_schedule_service_map_for_route(
        self, _build_service_map_from_paths, _ScheduledTripMatcher
    ):
        """[Service map manager] Calculate schedule service maps for system"""
        self.scheduledam.get_scheduled_trip_pk_to_path_in_system.return_value = {
            self.TRIP_1_PK: [1, 2, 3, 4],
            self.TRIP_2_PK: [3, 1, 0],
        }
        self.stopdam.get_stop_pk_to_station_pk_map_in_system.return_value = {
            0: 0,
            1: 11,
            2: 2,
            3: 3,
            4: 14,
        }
        self.trip_one.route_pk = self.ROUTE_1_PK
        self.trip_two.route_pk = self.ROUTE_1_PK
        self.scheduledam.list_scheduled_trips_with_times_in_system.return_value = [
            (self.trip_one, self.TRIP_1_START_TIME, self.TRIP_1_END_TIME),
            (self.trip_two, self.TRIP_2_START_TIME, self.TRIP_2_END_TIME),
        ]
        matcher = mock.MagicMock()
        _ScheduledTripMatcher.return_value = matcher
        matcher.return_value = True

        expected_paths = {(11, 2, 3, 14), (0, 11, 3)}

        servicemapmanager.calculate_scheduled_service_maps_for_system(self.system)

        _build_service_map_from_paths.assert_has_calls([mock.call(expected_paths)])

    def test_build_stop_pk_to_service_maps_response(self):
        """[Service map manager] Build service maps response"""

        route_1 = models.Route(id=self.ROUTE_1_ID)
        route_2 = models.Route(id=self.ROUTE_2_ID)
        self.servicemapdam.get_stop_pk_to_group_id_to_routes_map.return_value = {
            self.STOP_1_PK: {self.GROUP_ID: [route_1, route_2]}
        }

        expected = {
            self.STOP_1_PK: [
                {
                    "group_id": self.GROUP_ID,
                    "routes": [route_1.short_repr(), route_2.short_repr()],
                }
            ]
        }

        actual = servicemapmanager.build_stop_pk_to_service_maps_response(
            [self.STOP_1_PK]
        )

        self.assertEqual(expected, actual)

    def test_path_lists_to_sorted_graph__empty_list(self):
        """[Service pattern manager] Empty path list to sorted graph"""
        graph = mock.MagicMock()
        self.graphutils.graphdatastructs.DirectedPath.return_value = graph

        actual = servicemapmanager._build_sorted_graph_from_paths([])

        self.assertEqual(graph, actual)

        self.graphutils.graphdatastructs.DirectedPath.assert_called_once_with([])

    def test_path_lists_to_sorted_graph__single_list(self):
        """[Service pattern manager] Single path list to sorted graph"""
        path_list = mock.MagicMock()
        path_lists = [path_list]
        graph = mock.MagicMock()
        self.graphutils.graphdatastructs.DirectedPath.return_value = graph

        actual = servicemapmanager._build_sorted_graph_from_paths(path_lists)

        self.assertEqual(graph, actual)

        self.graphutils.graphdatastructs.DirectedPath.assert_called_once_with(path_list)

    def test_sorted_graph_to_service_pattern(self):
        """[Service pattern manager] Sorted graph to service pattern"""
        label_one = "1"
        label_two = "2"
        path_list = [label_one, label_two]
        graph = self.actual_graphutils.graphdatastructs.DirectedPath(path_list)

        stop_one = mock.MagicMock()
        stop_two = mock.MagicMock()
        label_to_stop = {label_one: stop_one, label_two: stop_two}

        expected_sp = models.ServiceMap()
        v_one = models.ServiceMapVertex()
        v_one.stop_pk = label_one
        v_one.map = expected_sp
        v_one.position = 0
        v_two = models.ServiceMapVertex()
        v_two.stop_pk = label_two
        v_two.map = expected_sp
        v_two.position = 1

        actual_sp = servicemapmanager._convert_sorted_graph_to_service_pattern(graph)

        self.assertEqual(expected_sp, actual_sp)
        self.assertEqual(expected_sp.vertices, actual_sp.vertices)

    def test_path_lists_to_sorted_graph__stiches_to_path(self):
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

        self.graphutils.graphdatastructs.DirectedPath.side_effect = DirectedPath

        graph = mock.MagicMock()
        self.graphutils.pathstitcher.stitch.return_value = graph
        graph.is_path.return_value = True
        final_graph = mock.MagicMock()
        graph.cast_to_path.return_value = final_graph

        actual = servicemapmanager._build_sorted_graph_from_paths(path_lists)

        self.assertEqual(final_graph, actual)

        self.graphutils.graphdatastructs.DirectedPath.assert_any_call(path_list_two)
        self.graphutils.graphdatastructs.DirectedPath.assert_any_call(path_list_one)
        self.graphutils.pathstitcher.stitch.assert_called_once_with(
            [directed_path_one, directed_path_two]
        )
        graph.is_path.assert_called_once_with()
        graph.cast_to_path.assert_called_once_with()
        self.graphutils.topologicalsort.sort.assert_not_called()

    def test_path_lists_to_sorted_graph__topological_sort(self):
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

        self.graphutils.graphdatastructs.DirectedPath.side_effect = DirectedPath

        graph = mock.MagicMock()
        self.graphutils.pathstitcher.stitch.return_value = graph
        graph.is_path.return_value = False
        final_graph = mock.MagicMock()
        self.graphutils.topologicalsort.sort.return_value = final_graph

        actual = servicemapmanager._build_sorted_graph_from_paths(path_lists)

        self.assertEqual(final_graph, actual)

        self.graphutils.graphdatastructs.DirectedPath.assert_any_call(path_list_two)
        self.graphutils.graphdatastructs.DirectedPath.assert_any_call(path_list_one)
        self.graphutils.pathstitcher.stitch.assert_called_once_with(
            [directed_path_one, directed_path_two]
        )
        graph.is_path.assert_called_once_with()
        graph.cast_to_path.assert_not_called()
        self.graphutils.topologicalsort.sort.assert_called_with(graph)


class TestTripMatcher(unittest.TestCase):
    DAYS = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]

    def setUp(self):
        self.early_weekday_trip = self._create_trip(
            {
                "start_time": datetime.time(hour=6, minute=0, second=0),
                "end_time": datetime.time(hour=8, minute=0, second=0),
                "monday": True,
                "route_id": "A",
            }
        )

        self.mid_weekday_trip = self._create_trip(
            {
                "start_time": datetime.time(hour=12, minute=0, second=0),
                "end_time": datetime.time(hour=14, minute=0, second=0),
                "tuesday": True,
                "route_id": "A",
            }
        )

        self.late_weekday_trip = self._create_trip(
            {
                "start_time": datetime.time(hour=22, minute=0, second=0),
                "end_time": datetime.time(hour=23, minute=0, second=0),
                "wednesday": True,
                "route_id": "B",
            }
        )

        self.early_weekend_trip = self._create_trip(
            {
                "start_time": datetime.time(hour=6, minute=0, second=0),
                "end_time": datetime.time(hour=8, minute=0, second=0),
                "sunday": True,
                "route_id": "C",
            }
        )

        self.trips = [
            self.early_weekday_trip,
            self.mid_weekday_trip,
            self.late_weekday_trip,
            self.early_weekend_trip,
        ]

    def test_one(self):
        """[Service map manager] trip matcher test 1"""
        raw_conds = {
            "weekday": True,
            "one_of": {"starts_earlier_than": 7, "starts_later_than": 20},
        }
        expected_trips = [self.early_weekday_trip, self.late_weekday_trip]

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    def test_two(self):
        """[Service map manager] trip matcher test 2"""
        raw_conds = {"all_of": {"starts_earlier_than": 7, "starts_later_than": 7.01}}
        expected_trips = []

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    def test_three(self):
        """[Service map manager] trip matcher test 3"""
        raw_conds = {"weekday": True, "starts_later_than": 7, "starts_earlier_than": 20}
        expected_trips = [self.mid_weekday_trip]

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    def test_four(self):
        """[Service map manager] trip matcher test 4"""
        raw_conds = {"none_of": {"ends_later_than": 13}}
        expected_trips = [self.early_weekday_trip, self.early_weekend_trip]

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    def test_five(self):
        """[Service map manager] trip matcher test 5"""
        raw_conds = {"all_of": {"ends_earlier_than": 11, "weekday": True}}
        expected_trips = [self.early_weekday_trip]

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    def test_six(self):
        """[Service map manager] trip matcher test 6"""
        raw_conds = {"weekend": True}
        expected_trips = [self.early_weekend_trip]

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    def _test_seven(self):
        """[Service map manager] trip matcher test 7"""
        raw_conds = {"route_id": "A"}
        expected_trips = [self.early_weekday_trip, self.mid_weekday_trip]

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    def _test_eight(self):
        """[Service map manager] trip matcher test 8"""
        raw_conds = {"route_id": ["B", "C"]}
        expected_trips = [self.late_weekday_trip, self.early_weekend_trip]

        matched_trips = self._trip_matcher_runner(raw_conds, self.trips)

        self.assertListEqual(matched_trips, expected_trips)

    def test_nine(self):
        """[Service map manager] trip matcher test 9"""
        raw_conds = {"unknown_condition": True}

        self.assertRaises(
            NotImplementedError, self._trip_matcher_runner, raw_conds, self.trips
        )

    @staticmethod
    def _trip_matcher_runner(raw_conds, trips):
        trips_matcher = servicemapmanager._ScheduledTripMatcher(raw_conds)
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
