import pytest

from transiter import exceptions
from transiter.db import models
from transiter.db.queries import alertqueries, tripqueries, routequeries
from transiter.services import tripservice, views


def test_list_all_in_route__route_not_found(monkeypatch, route_1_model):
    monkeypatch.setattr(
        routequeries, "get_in_system_by_id", lambda *args, **kwargs: None
    )

    with pytest.raises(exceptions.IdNotFoundError):
        tripservice.list_all_in_route(route_1_model.system.id, route_1_model.id)


def test_list_all_in_route(
    monkeypatch,
    route_1_model,
    trip_1_model,
    trip_1_view,
    trip_2_model,
    trip_2_view,
    stop_1_model,
    stop_1_small_view,
    stop_2_model,
    stop_2_small_view,
):
    monkeypatch.setattr(
        routequeries, "get_in_system_by_id", lambda *args, **kwargs: route_1_model
    )
    monkeypatch.setattr(
        tripqueries,
        "list_all_in_route_by_pk",
        lambda *args, **kwargs: [trip_1_model, trip_2_model],
    )
    monkeypatch.setattr(
        tripqueries,
        "get_trip_pk_to_last_stop_map",
        lambda *args, **kwargs: {
            trip_1_model.pk: stop_1_model,
            trip_2_model.pk: stop_2_model,
        },
    )
    monkeypatch.setattr(
        alertqueries, "get_trip_pk_to_active_alerts", lambda *args, **kwargs: {}
    )

    expected = [trip_1_view, trip_2_view]

    expected[0].last_stop = stop_1_small_view
    expected[0].alerts = []
    expected[1].last_stop = stop_2_small_view
    expected[1].alerts = []

    actual = tripservice.list_all_in_route(route_1_model.system.id, route_1_model.id)

    assert expected == actual


def test_get_in_route_by_id__trip_not_found(monkeypatch, trip_1_model):
    monkeypatch.setattr(tripqueries, "get_in_route_by_id", lambda *args, **kwargs: None)

    with pytest.raises(exceptions.IdNotFoundError):
        tripservice.get_in_route_by_id(
            trip_1_model.route.system.id, trip_1_model.route.id, trip_1_model.id
        )


def test_get_in_route_by_id(
    monkeypatch,
    route_1_model,
    route_1_small_view,
    trip_1_model,
    trip_1_view,
    stop_1_model,
    stop_1_small_view,
):
    monkeypatch.setattr(
        tripqueries, "get_in_route_by_id", lambda *args, **kwargs: trip_1_model
    )
    monkeypatch.setattr(
        alertqueries, "get_trip_pk_to_active_alerts", lambda *args, **kwargs: {}
    )

    stop_time = models.TripStopTime(stop_sequence=1)
    stop_time.stop = stop_1_model
    trip_1_model.stop_times = [stop_time]

    expected = trip_1_view
    expected.stop_times = [views.TripStopTime.from_model(stop_time)]
    expected.alerts = []
    expected.route = route_1_small_view
    expected.stop_times[0].stop = stop_1_small_view

    actual = tripservice.get_in_route_by_id(
        trip_1_model.route.system.id, trip_1_model.route.id, trip_1_model.id
    )

    assert expected == actual
