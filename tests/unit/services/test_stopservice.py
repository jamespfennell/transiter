import datetime
import time
import unittest.mock as mock

import pytest

from transiter import models, exceptions
from transiter.data import tripqueries, systemqueries, stopqueries
from transiter.services import stopservice, views
from transiter.services.servicemap import servicemapmanager

SYSTEM_ID = "1"
STOP_ONE_ID = "2"
STOP_ONE_PK = 3
STOP_ONE_NAME = "Name"
TRIP_PK = 100
TRIP_ID = "101"
ROUTE_ID = "103"
STOP_TWO_ID = "102"
STOP_TWO_NAME = "102-NAME"
DIRECTION_NAME = "Uptown"
TRIP_STOP_TIME_ONE_PK = 201
TRIP_STOP_TIME_TWO_PK = 202
DIRECTION = "Left"
TIME_1 = datetime.datetime(4, 4, 4, 4, 10, 0)
TIME_2 = datetime.datetime(4, 4, 4, 4, 15, 0)
TIME_3 = datetime.datetime(4, 4, 4, 4, 20, 0)
TIME_4 = datetime.datetime(4, 4, 4, 4, 25, 0)


@pytest.fixture
def time_dot_time(monkeypatch):
    mocked_time_dot_time = mock.MagicMock()
    monkeypatch.setattr(time, "time", mocked_time_dot_time)
    return mocked_time_dot_time


def test_old_trips__exclude(time_dot_time):

    stop_time = models.TripStopTime(arrival_time=TIME_1)
    time_dot_time.return_value = TIME_4.timestamp()

    stop_time_filter = stopservice._TripStopTimeFilter("0", "10", "0")

    assert stop_time_filter.remove(stop_time, DIRECTION) is True


def test_old_trips__include_when_no_lower_bound(time_dot_time):
    stop_time = models.TripStopTime(arrival_time=TIME_1)
    time_dot_time.return_value = TIME_4.timestamp()

    stop_time_filter = stopservice._TripStopTimeFilter(None, "10", "0")

    assert stop_time_filter.remove(stop_time, DIRECTION) is False


def test_old_trips__include_selectively(time_dot_time):
    stop_times = [
        models.TripStopTime(arrival_time=TIME_1),
        models.TripStopTime(arrival_time=TIME_2),
    ]
    time_dot_time.return_value = TIME_3.timestamp()

    stop_time_filter = stopservice._TripStopTimeFilter("7.5", "10", "0")

    assert stop_time_filter.remove(stop_times[0], DIRECTION) is True
    assert stop_time_filter.remove(stop_times[1], DIRECTION) is False


def test_direction(time_dot_time):

    stop_times = [
        models.TripStopTime(arrival_time=TIME_2),
        models.TripStopTime(arrival_time=TIME_3),
    ]
    time_dot_time.return_value = TIME_1.timestamp()

    stop_time_filter = stopservice._TripStopTimeFilter("0", "0", "1")

    assert stop_time_filter.remove(stop_times[0], DIRECTION) is False
    assert stop_time_filter.remove(stop_times[1], DIRECTION) is True


def test_direction_name_matcher__all_names():
    matcher = stopservice._DirectionNameMatcher(
        [models.DirectionRule(stop_pk=1, name=DIRECTION_NAME)]
    )

    assert {DIRECTION_NAME} == matcher.all_names()


@pytest.mark.parametrize(
    "direction_rule,expected",
    [
        [models.DirectionRule(stop_pk=1, name=DIRECTION_NAME), DIRECTION_NAME],
        [models.DirectionRule(stop_pk=2, name=DIRECTION_NAME), None],
        [models.DirectionRule(stop_pk=1, name=DIRECTION_NAME, direction_id=True), None],
        [models.DirectionRule(stop_pk=1, name=DIRECTION_NAME, track="track"), None],
    ],
)
def test_direction_name_matcher__match(direction_rule, expected):
    matcher = stopservice._DirectionNameMatcher([direction_rule])
    stop_time = models.TripStopTime(stop_pk=1, trip=models.Trip())

    actual = matcher.match(stop_time)

    assert expected == actual


def test_list_all_in_system(monkeypatch):
    system = models.System(id=SYSTEM_ID)
    stop_one = models.Stop(
        pk=STOP_ONE_PK, id=STOP_ONE_ID, name=STOP_ONE_NAME, system=system
    )
    monkeypatch.setattr(systemqueries, "get_by_id", lambda *args, **kwargs: system)
    monkeypatch.setattr(stopqueries, "list_all_in_system", lambda *args: [stop_one])

    expected = [views.Stop(id=STOP_ONE_ID, name=STOP_ONE_NAME, _system_id=SYSTEM_ID)]

    actual = stopservice.list_all_in_system(SYSTEM_ID)

    assert expected == actual


def test_list_all_in_system__system_not_found(monkeypatch):

    monkeypatch.setattr(systemqueries, "get_by_id", lambda *args, **kwargs: None)

    with pytest.raises(exceptions.IdNotFoundError):
        stopservice.list_all_in_system(SYSTEM_ID)


def test_get_in_system_by_id__stop_not_found(monkeypatch):
    monkeypatch.setattr(stopqueries, "get_in_system_by_id", lambda *args: None)

    with pytest.raises(exceptions.IdNotFoundError):
        stopservice.get_in_system_by_id(SYSTEM_ID, STOP_ONE_ID),


def test_get_in_system_by_id(monkeypatch):
    stop_one = models.Stop(
        pk=STOP_ONE_PK, id=STOP_ONE_ID, system=models.System(id=SYSTEM_ID),
    )
    stop_time_one = models.TripStopTime(
        pk=TRIP_STOP_TIME_ONE_PK, arrival_time=datetime.datetime(2000, 1, 1, 0, 0, 0),
    )
    stop_time_two = models.TripStopTime(
        pk=TRIP_STOP_TIME_TWO_PK, arrival_time=datetime.datetime(2137, 1, 1, 0, 0, 0),
    )

    child_stops = mock.MagicMock()
    parent_stop = mock.MagicMock()

    monkeypatch.setattr(stopqueries, "get_in_system_by_id", lambda *args: stop_one)
    monkeypatch.setattr(
        stopqueries, "list_all_stops_in_stop_tree", lambda *args: [stop_one]
    )
    monkeypatch.setattr(stopqueries, "list_direction_rules_for_stops", lambda *args: [])
    monkeypatch.setattr(
        stopqueries,
        "list_stop_time_updates_at_stops",
        lambda *args, **kwargs: [stop_time_one, stop_time_two],
    )

    monkeypatch.setattr(tripqueries, "get_trip_pk_to_last_stop_map", mock.MagicMock())
    monkeypatch.setattr(
        servicemapmanager, "build_stop_pk_to_service_maps_response", mock.MagicMock()
    )

    monkeypatch.setattr(
        stopservice._DirectionNameMatcher, "match", lambda *args: DIRECTION_NAME
    )
    monkeypatch.setattr(
        stopservice._DirectionNameMatcher, "all_names", lambda *args: [DIRECTION_NAME]
    )
    fake_stop_tree_response = views.Stop(
        id=STOP_TWO_ID,
        name=None,
        _system_id=SYSTEM_ID,
        child_stops=child_stops,
        parent_stop=parent_stop,
    )
    monkeypatch.setattr(
        stopservice, "_build_stop_tree_response", lambda *args: fake_stop_tree_response
    )
    fake_trip_stop_time_response = mock.MagicMock()
    monkeypatch.setattr(
        stopservice,
        "_build_trip_stop_time_response",
        lambda *args: fake_trip_stop_time_response,
    )

    expected = views.StopLarge(
        id=STOP_ONE_ID,
        name=None,
        latitude=None,
        longitude=None,
        url=None,
        _system_id=SYSTEM_ID,
        parent_stop=parent_stop,
        child_stops=child_stops,
        directions=[DIRECTION_NAME],
        stop_times=[fake_trip_stop_time_response],
    )

    actual = stopservice.get_in_system_by_id(
        SYSTEM_ID, STOP_ONE_ID, exclude_trips_before=1
    )

    assert expected == actual


def test_build_trip_stop_time_response():
    system = models.System(id=SYSTEM_ID)
    stop = models.Stop(system=system)
    stop.id = STOP_ONE_ID
    trip = models.Trip()
    trip.pk = TRIP_PK
    trip.id = TRIP_ID
    trip_stop_time = models.TripStopTime(arrival_time=TIME_1, departure_time=TIME_2)
    trip_stop_time.trip = trip
    trip_stop_time.stop = stop
    route = models.Route(system=system)
    route.id = ROUTE_ID
    trip.route = route
    last_stop = models.Stop(system=system, id=STOP_TWO_ID, name=STOP_TWO_NAME)
    last_stop.id = STOP_TWO_ID

    expected = views.TripStopTime(
        arrival=views._TripStopTimeEvent(time=TIME_1, delay=None, uncertainty=None),
        departure=views._TripStopTimeEvent(time=TIME_2, delay=None, uncertainty=None),
        track=None,
        future=None,
        stop_sequence=None,
        direction=DIRECTION_NAME,
        trip=views.Trip(
            id=TRIP_ID,
            current_status=None,
            current_stop_sequence=None,
            direction_id=None,
            last_update_time=None,
            vehicle_id=None,
            start_time=None,
            _route_id=ROUTE_ID,
            _system_id=SYSTEM_ID,
            route=views.Route(id=ROUTE_ID, color=None, _system_id=SYSTEM_ID),
            last_stop=views.Stop(
                id=STOP_TWO_ID, name=STOP_TWO_NAME, _system_id=SYSTEM_ID
            ),
        ),
    )

    actual = stopservice._build_trip_stop_time_response(
        trip_stop_time, DIRECTION_NAME, {trip.pk: last_stop}
    )

    assert expected == actual


def tree_factory(number_of_stops, adjacency_tuples, not_stations=None):
    system = models.System(id="system_id")
    stops = [
        models.Stop(pk=i, id=str(i), type=models.Stop.Type.STATION, system=system)
        for i in range(number_of_stops)
    ]
    for stop_pk, parent_pk in adjacency_tuples:
        stops[stop_pk].parent_stop_pk = parent_pk
    if not_stations is not None:
        for not_station in not_stations:
            stops[not_station].type = models.Stop.Type.PLATFORM
    return stops


@pytest.fixture
def tree_1():
    #     0
    #    / \
    #   1   2
    #  /
    # 3*
    # * not a station
    return tree_factory(4, [(1, 0), (2, 0), (3, 1)], [3])


@pytest.fixture
def tree_2():
    #      2
    #    / | \
    #   1  3  4
    #  /   |
    # 0    5*
    # * not a station
    return tree_factory(6, [(1, 2), (0, 1), (3, 2), (5, 3), (4, 2)], [5])


@pytest.fixture
def trees(tree_1, tree_2):
    return [tree_1, tree_2]


def test_build_stop_tree_response(tree_1):
    stop_tree = stopservice._StopTree(tree_1[1], tree_1)

    stop_pk_to_service_maps_response = {pk: pk for pk in range(4)}

    system_id = tree_1[1].system.id

    expected = views.Stop(
        id=tree_1[1].id,
        name=None,
        _system_id=system_id,
        service_maps=1,
        parent_stop=views.Stop(
            id=tree_1[0].id,
            name=None,
            _system_id=system_id,
            service_maps=0,
            parent_stop=None,
            child_stops=[
                views.Stop(
                    id=tree_1[2].id,
                    name=None,
                    _system_id=system_id,
                    service_maps=2,
                    child_stops=[],
                )
            ],
        ),
        child_stops=[],
    )

    actual = stopservice._build_stop_tree_response(
        stop_tree, stop_pk_to_service_maps_response, True
    )

    assert expected == actual


# fmt: off
@pytest.mark.parametrize(
    "tree_number,base_index,expected",
    [
        [1, 0, [3, 1, 2, 0]],
        [1, 1, [3, 1]],
        [2, 2, [0, 1, 5, 3, 4, 2]],
        [2, 0, [0]]
    ],
)
# fmt: on
def test_stop_tree__descendent(tree_number, base_index, expected, trees):
    tree = trees[tree_number - 1]

    actual = [
        stop.pk for stop in stopservice._StopTree(tree[base_index], tree).descendents()
    ]

    assert expected == actual


@pytest.mark.parametrize(
    "tree_number,base_index,expected",
    [
        [1, 0, [1, 2, 0]],
        [1, 1, [2, 0, 1]],
        [1, 3, [2, 0, 1, 3]],
        [2, 2, [0, 1, 3, 4, 2]],
        [2, 1, [3, 4, 2, 0, 1]],
        [2, 0, [3, 4, 2, 1, 0]],
        [2, 3, [0, 1, 4, 2, 3]],
    ],
)
def test_stop_tree__all_stations(tree_number, base_index, expected, trees):
    tree = trees[tree_number - 1]

    actual = [
        stop.pk for stop in stopservice._StopTree(tree[base_index], tree).all_stations()
    ]

    assert expected == actual


@pytest.mark.parametrize("only_stations", [True, False])
def test_stop_tree__apply_function(tree_1, only_stations):
    def function(stop, parent_response, children_responses):
        response = {"pk": stop.pk, "children": children_responses}
        if stop.parent_stop_pk is None:
            response["parent"] = None
        elif parent_response is not None:
            response["parent"] = parent_response
        return response

    # fmt: off
    expected = {
        "pk": 1,
        "parent": {
            "pk": 0,
            "children": [
                {
                    "pk": 2,
                    "children": [],
                },
            ],
            "parent": None
        },
        "children": []
    }
    if not only_stations:
        expected["children"].append(
            {
                "pk": 3,
                "children": []
            }
        )
    # fmt: on

    assert expected == stopservice._StopTree(tree_1[1], tree_1).apply_function(
        function, only_stations=only_stations
    )
