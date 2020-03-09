import pytest

from transiter import models, exceptions
from transiter.data.dams import tripdam, routedam
from transiter.services import tripservice, links

SYSTEM_ID = "1"
ROUTE_ID = "2"
TRIP_ONE_ID = "3"
TRIP_ONE_PK = 4
TRIP_TWO_ID = "5"
TRIP_TWO_PK = 6
STOP_ONE_ID = "7"
STOP_TWO_ID = "8"


@pytest.fixture
def system():
    return models.System(id=SYSTEM_ID)


@pytest.fixture
def route(system):
    return models.Route(id=ROUTE_ID, system=system)


@pytest.fixture
def trip_1(route):
    return models.Trip(pk=TRIP_ONE_PK, id=TRIP_ONE_ID, route=route)


@pytest.fixture
def trip_2(route):
    return models.Trip(pk=TRIP_TWO_PK, id=TRIP_TWO_ID, route=route)


@pytest.fixture
def stop_1(system):
    return models.Stop(id=STOP_ONE_ID, system=system)


@pytest.fixture
def stop_2(system):
    return models.Stop(id=STOP_TWO_ID, system=system)


def test_list_all_in_route__route_not_found(monkeypatch):
    """[Trip service] List all in route - route not found"""
    monkeypatch.setattr(routedam, "get_in_system_by_id", lambda *args, **kwargs: None)

    with pytest.raises(exceptions.IdNotFoundError):
        tripservice.list_all_in_route(SYSTEM_ID, ROUTE_ID),


def test_list_all_in_route(monkeypatch, route, trip_1, trip_2, stop_1, stop_2):
    """[Trip service] List all trips in a route"""
    monkeypatch.setattr(routedam, "get_in_system_by_id", lambda *args, **kwargs: route)
    monkeypatch.setattr(
        tripdam, "list_all_in_route_by_pk", lambda *args, **kwargs: [trip_1, trip_2]
    )
    monkeypatch.setattr(
        tripdam,
        "get_trip_pk_to_last_stop_map",
        lambda *args, **kwargs: {trip_1.pk: stop_1, trip_2.pk: stop_2},
    )

    expected = [
        {
            **trip_1.to_dict(),
            "last_stop": {**stop_1.to_dict(), "href": links.StopEntityLink(stop_1)},
            "href": links.TripEntityLink(trip_1),
        },
        {
            **trip_2.to_dict(),
            "last_stop": {**stop_2.to_dict(), "href": links.StopEntityLink(stop_2)},
            "href": links.TripEntityLink(trip_2),
        },
    ]

    actual = tripservice.list_all_in_route(SYSTEM_ID, ROUTE_ID, True)

    assert expected == actual


def test_get_in_route_by_id__trip_not_found(monkeypatch):
    """[Trip service] Get in route - trip not found"""
    monkeypatch.setattr(tripdam, "get_in_route_by_id", lambda *args, **kwargs: None)

    with pytest.raises(exceptions.IdNotFoundError):
        tripservice.get_in_route_by_id(SYSTEM_ID, ROUTE_ID, TRIP_ONE_ID),


def test_get_in_route_by_id(monkeypatch, route, trip_1, stop_1):
    """[Trip service] Get in in route"""

    monkeypatch.setattr(tripdam, "get_in_route_by_id", lambda *args, **kwargs: trip_1)

    stop_time = models.TripStopTime()
    stop_time.stop = stop_1
    trip_1.stop_times = [stop_time]

    expected = {
        **trip_1.to_large_dict(),
        "route": {**route.to_dict(), "href": links.RouteEntityLink(route)},
        "stop_times": [
            {
                **stop_time.to_dict(),
                "stop": {**stop_1.to_dict(), "href": links.StopEntityLink(stop_1)},
            }
        ],
    }

    actual = tripservice.get_in_route_by_id(SYSTEM_ID, ROUTE_ID, TRIP_ONE_ID, True)

    assert expected == actual
