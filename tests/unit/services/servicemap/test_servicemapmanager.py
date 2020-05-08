import datetime
import unittest
from unittest import mock

import pytest

from transiter import models
from transiter.data import (
    dbconnection,
    tripqueries,
    servicemapqueries,
    schedulequeries,
    stopqueries,
)
from transiter.services import views
from transiter.services.servicemap import servicemapmanager
from transiter.services.servicemap.graphutils import datastructures

SYSTEM_ID = "system_id"
SYSTEM_PK = 101
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


def test_calculate_realtime_service_map_for_route(monkeypatch):
    service_map_group = models.ServiceMapGroup(
        source=models.ServiceMapGroup.ServiceMapSource.REALTIME
    )
    route_1 = models.Route(
        pk=ROUTE_1_PK,
        id=ROUTE_1_ID,
        system=models.System(service_map_groups=[service_map_group]),
        trips=[
            models.Trip(pk=TRIP_1_PK, direction_id=True),
            models.Trip(pk=TRIP_2_PK, direction_id=False),
        ],
    )

    monkeypatch.setattr(
        tripqueries,
        "get_trip_pk_to_path_map",
        lambda *args, **kwargs: {TRIP_1_PK: [1, 2, 3, 4], TRIP_2_PK: [3, 1, 0]},
    )
    monkeypatch.setattr(
        stopqueries,
        "get_stop_pk_to_station_pk_map_in_system",
        lambda *args, **kwargs: {0: 0, 1: 11, 2: 2, 3: 3, 4: 14},
    )

    new_service_map = models.ServiceMap()
    _build_service_map_from_paths = mock.MagicMock()
    monkeypatch.setattr(
        servicemapmanager,
        "_build_service_map_from_paths",
        _build_service_map_from_paths,
    )
    _build_service_map_from_paths.return_value = new_service_map

    expected_paths = {(11, 2, 3, 14), (0, 11, 3)}

    servicemapmanager.calculate_realtime_service_map_for_route(route_1)

    _build_service_map_from_paths.assert_called_once_with(expected_paths)
    assert route_1 == new_service_map.route
    assert service_map_group == new_service_map.group


def test_calculate_schedule_service_map_for_route(monkeypatch):
    monkeypatch.setattr(dbconnection, "get_session", mock.MagicMock())
    monkeypatch.setattr(
        schedulequeries,
        "get_scheduled_trip_pk_to_path_in_system",
        lambda *args, **kwargs: {TRIP_1_PK: [1, 2, 3, 4], TRIP_2_PK: [3, 1, 0]},
    )
    monkeypatch.setattr(
        stopqueries,
        "get_stop_pk_to_station_pk_map_in_system",
        lambda *args, **kwargs: {0: 0, 1: 11, 2: 2, 3: 3, 4: 14},
    )
    system = models.System(
        id=SYSTEM_ID,
        pk=SYSTEM_PK,
        service_map_groups=[
            models.ServiceMapGroup(
                source=models.ServiceMapGroup.ServiceMapSource.SCHEDULE, threshold=0.05
            )
        ],
    )
    trip_one = models.ScheduledTrip(
        pk=TRIP_1_PK, route_pk=ROUTE_1_PK, direction_id=True
    )
    trip_two = models.ScheduledTrip(
        pk=TRIP_2_PK, route_pk=ROUTE_1_PK, direction_id=False
    )
    monkeypatch.setattr(
        schedulequeries,
        "list_scheduled_trips_with_times_in_system",
        lambda *args, **kwargs: [
            (trip_one, TRIP_1_START_TIME, TRIP_1_END_TIME),
            (trip_two, TRIP_2_START_TIME, TRIP_2_END_TIME),
        ],
    )
    matcher = mock.MagicMock()
    matcher.return_value = True
    monkeypatch.setattr(
        servicemapmanager, "_ScheduledTripMatcher", lambda *args, **kwargs: matcher
    )

    _build_service_map_from_paths = mock.MagicMock()
    monkeypatch.setattr(
        servicemapmanager,
        "_build_service_map_from_paths",
        _build_service_map_from_paths,
    )

    expected_paths = {(11, 2, 3, 14), (0, 11, 3)}

    servicemapmanager.calculate_scheduled_service_maps_for_system(system)

    _build_service_map_from_paths.assert_has_calls([mock.call(expected_paths)])


def test_build_stop_pk_to_service_maps_response(monkeypatch):
    system = models.System(id=SYSTEM_ID)
    route_1 = models.Route(id=ROUTE_1_ID, system=system)
    route_2 = models.Route(id=ROUTE_2_ID, system=system)

    monkeypatch.setattr(
        servicemapmanager,
        "build_stop_pk_to_group_id_to_inherited_routes_map",
        lambda *args: {STOP_1_PK: {GROUP_ID: [route_1, route_2]}},
    )

    expected = {
        STOP_1_PK: [
            views.ServiceMapWithRoutes(
                GROUP_ID,
                [
                    views.Route(ROUTE_1_ID, None, SYSTEM_ID),
                    views.Route(ROUTE_2_ID, None, SYSTEM_ID),
                ],
            )
        ]
    }

    actual = servicemapmanager.build_stop_pk_to_service_maps_response([STOP_1_PK])

    assert expected == actual


def test_build_stop_pk_to_group_id_to_inherited_routes_map(monkeypatch):
    monkeypatch.setattr(
        stopqueries,
        "build_stop_pk_to_descendant_pks_map",
        lambda *args, **kwargs: {1: [1, 2, 3]},
    )
    monkeypatch.setattr(
        servicemapqueries,
        "get_stop_pk_to_group_id_to_routes_map",
        lambda *args: {
            2: {"group": [models.Route(id="2"), models.Route(id="3")]},
            3: {"group": [models.Route(id="4"), models.Route(id="1")]},
        },
    )

    expected_result = {
        1: {
            "group": [
                models.Route(id="1"),
                models.Route(id="2"),
                models.Route(id="3"),
                models.Route(id="4"),
            ]
        }
    }

    actual_result = servicemapmanager.build_stop_pk_to_group_id_to_inherited_routes_map(
        [1]
    )

    assert expected_result == actual_result


def test_build_sorted_graph_from_paths__empty_graph():
    empty_graph = datastructures.Graph.build_from_edge_label_tuples([])

    assert servicemapmanager._build_sorted_graph_from_paths(set()) == [empty_graph]


def test_build_sorted_graph_from_paths__path():
    path = datastructures.Graph.build_from_edge_label_tuples(
        [("a", "b"), ("b", "c"), ("c", "d")]
    )

    assert servicemapmanager._build_sorted_graph_from_paths({("a", "b", "c", "d")}) == [
        path
    ]


def test_build_sorted_graph_from_paths__full_case():
    raw_paths = [("a", "b", "c"), ("a", "c", "d"), ("x", "y", "z")]

    path_1 = datastructures.Graph.build_from_edge_label_tuples(
        [("a", "b"), ("b", "c"), ("c", "d"), ("a", "c")]
    )
    path_2 = datastructures.Graph.build_from_edge_label_tuples([("x", "y"), ("y", "z")])

    graphs = servicemapmanager._build_sorted_graph_from_paths(set(raw_paths))

    assert [path_1, path_2] == graphs or [path_2, path_1] == graphs


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


@pytest.mark.parametrize(
    "paths_1,paths_2,should_match",
    [
        [[(1, 3, 4)], [(1, 3, 4), (1, 3)], True],
        [[(1, 3, 4)], [(1, 3)], True],
        [[(1, 3, 4)], [(1, 3, 4)], True],
        [[(1, 3, 4)], [(1, 4)], False],
    ],
)
def test_calculate_paths_hash(paths_1, paths_2, should_match):
    paths_1 = [(1, 3, 4)]
    paths_2 = [(1, 3, 4), (1, 3)]
    should_match = True

    hash_1 = servicemapmanager.calculate_paths_hash(paths_1)
    hash_2 = servicemapmanager.calculate_paths_hash(paths_2)
    hashes_match = hash_1 == hash_2

    assert hashes_match == should_match


def test_calculate_changed_route_pks_from_hashes():

    dict_1 = {3: "hash_a", 4: "hash_b", 5: "hash_f"}
    dict_2 = {2: "hash_c", 3: "hash_a", 4: "hash_e"}

    assert {2, 4, 5} == servicemapmanager.calculate_changed_route_pks_from_hashes(
        dict_1, dict_2
    )
