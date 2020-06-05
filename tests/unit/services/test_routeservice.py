import pytest

from transiter import exceptions
from transiter.db.queries import alertqueries, routequeries, systemqueries
from transiter.services import routeservice, views
from transiter.services.servicemap import servicemapmanager

RAW_FREQUENCY = 700


def test_list_all_in_system__system_not_found(monkeypatch, system_1_model):
    monkeypatch.setattr(systemqueries, "get_by_id", lambda *args, **kwargs: None)

    with pytest.raises(exceptions.IdNotFoundError):
        routeservice.list_all_in_system(system_1_model.id)


@pytest.mark.parametrize("return_alerts", [True, False])
def test_list_all_in_system(
    monkeypatch,
    system_1_model,
    route_1_model,
    route_1_small_view,
    route_2_small_view,
    route_2_model,
    alert_1_model,
    alert_1_small_view,
    return_alerts,
):
    monkeypatch.setattr(
        systemqueries, "get_by_id", lambda *args, **kwargs: system_1_model
    )
    monkeypatch.setattr(
        routequeries,
        "list_in_system",
        lambda *args, **kwargs: [route_1_model, route_2_model],
    )
    monkeypatch.setattr(
        alertqueries,
        "get_route_pk_to_active_alerts",
        lambda *args, **kwargs: {
            route_1_model.pk: [(alert_1_model.active_periods[0], alert_1_model)],
            route_2_model.pk: [],
        },
    )

    expected = [route_1_small_view, route_2_small_view]
    if return_alerts:
        expected[0].alerts = [alert_1_small_view]
        expected[1].alerts = []

    actual = routeservice.list_all_in_system(
        route_1_model.system.id, None if return_alerts else views.AlertsDetail.NONE
    )

    assert actual == expected


def test_get_in_system_by_id__route_not_found(monkeypatch, route_1_model):
    monkeypatch.setattr(routequeries, "get_in_system_by_id", lambda *args: None)

    with pytest.raises(exceptions.IdNotFoundError):
        routeservice.get_in_system_by_id(route_1_model.system.id, route_1_model.id)


@pytest.mark.parametrize("return_alerts", [True, False])
def test_get_in_system_by_id(
    monkeypatch,
    route_1_model,
    route_1_large_view,
    alert_1_large_view,
    alert_1_model,
    return_alerts,
):
    monkeypatch.setattr(
        routequeries, "get_in_system_by_id", lambda *args: route_1_model
    )
    monkeypatch.setattr(
        routequeries, "calculate_periodicity", lambda *args: RAW_FREQUENCY
    )
    monkeypatch.setattr(
        alertqueries,
        "get_route_pk_to_active_alerts",
        lambda *args, **kwargs: {
            route_1_model.pk: [(alert_1_model.active_periods[0], alert_1_model)]
        },
    )
    monkeypatch.setattr(
        servicemapmanager, "build_route_service_maps_response", lambda *args: []
    )

    expected = route_1_large_view
    route_1_large_view.periodicity = int(RAW_FREQUENCY / 6) / 10
    if return_alerts:
        expected.alerts = [alert_1_large_view]

    actual = routeservice.get_in_system_by_id(
        route_1_model.system.id,
        route_1_model.id,
        None if return_alerts else views.AlertsDetail.NONE,
    )

    assert expected == actual
