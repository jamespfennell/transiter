import datetime

import pytest

from transiter import exceptions
from transiter.db import models
from transiter.db.queries import alertqueries, routequeries, systemqueries
from transiter.services import routeservice, views
from transiter.services.servicemap import servicemapmanager

SYSTEM_ID = "1"
ROUTE_ONE_PK = 2
ROUTE_ONE_ID = "3"
ROUTE_TWO_PK = 4
ROUTE_TWO_ID = "5"
ALERT_ID = "6"
ALERT_HEADER = "Header"
ALERT_DESCRIPTION = "Description"
RAW_FREQUENCY = 700
SERVICE_MAP_ONE_GROUP_ID = "1000"
SERVICE_MAP_TWO_GROUP_ID = "1001"
STOP_ID = "1002"
TIME_1 = datetime.datetime.utcfromtimestamp(1000)
TIME_2 = datetime.datetime.utcfromtimestamp(2000)


@pytest.fixture
def alert_1_model():
    return models.Alert(
        id=ALERT_ID,
        cause=models.Alert.Cause.UNKNOWN_CAUSE,
        effect=models.Alert.Effect.UNKNOWN_EFFECT,
        active_periods=[models.AlertActivePeriod(starts_at=TIME_1, ends_at=TIME_2)],
        messages=[
            models.AlertMessage(header=ALERT_HEADER, description=ALERT_DESCRIPTION)
        ],
    )


@pytest.fixture
def alert_1_small_view():
    return views.AlertSmall(
        id=ALERT_ID,
        cause=models.Alert.Cause.UNKNOWN_CAUSE,
        effect=models.Alert.Effect.UNKNOWN_EFFECT,
    )


@pytest.fixture
def alert_1_large_view():
    return views.AlertLarge(
        id=ALERT_ID,
        cause=models.Alert.Cause.UNKNOWN_CAUSE,
        effect=models.Alert.Effect.UNKNOWN_EFFECT,
        active_period=views.AlertActivePeriod(starts_at=TIME_1, ends_at=TIME_2),
        messages=[
            views.AlertMessage(header=ALERT_HEADER, description=ALERT_DESCRIPTION)
        ],
    )


@pytest.fixture
def system_1_model():
    return models.System(id=SYSTEM_ID)


@pytest.fixture
def route_1_model(system_1_model):
    return models.Route(
        system=system_1_model,
        id=ROUTE_ONE_ID,
        color="route_1_color",
        short_name="route_1_short_name",
        long_name="route_1_long_name",
        description="route_1_description",
        url="route_1_url",
        type=models.Route.Type.FUNICULAR,
        pk=ROUTE_ONE_PK,
    )


@pytest.fixture
def route_1_small_view():
    return views.Route(id=ROUTE_ONE_ID, color="route_1_color", _system_id=SYSTEM_ID)


@pytest.fixture
def route_1_large_view():
    return views.RouteLarge(
        id=ROUTE_ONE_ID,
        periodicity=0,
        color="route_1_color",
        short_name="route_1_short_name",
        long_name="route_1_long_name",
        description="route_1_description",
        url="route_1_url",
        type=models.Route.Type.FUNICULAR,
        _system_id=SYSTEM_ID,
    )


@pytest.fixture
def route_2_model(system_1_model):
    return models.Route(
        system=system_1_model, id=ROUTE_TWO_ID, color="route_2_color", pk=ROUTE_TWO_PK
    )


@pytest.fixture
def route_2_small_view():
    return views.Route(id=ROUTE_TWO_ID, color="route_2_color", _system_id=SYSTEM_ID)


def test_list_all_in_system__system_not_found(monkeypatch):
    monkeypatch.setattr(systemqueries, "get_by_id", lambda *args, **kwargs: None)

    with pytest.raises(exceptions.IdNotFoundError):
        routeservice.list_all_in_system(SYSTEM_ID)


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
            ROUTE_ONE_PK: [(alert_1_model.active_periods[0], alert_1_model)],
            ROUTE_TWO_PK: [],
        },
    )

    expected = [route_1_small_view, route_2_small_view]
    if return_alerts:
        expected[0].alerts = [alert_1_small_view]
        expected[1].alerts = []

    actual = routeservice.list_all_in_system(
        SYSTEM_ID, None if return_alerts else views.AlertsDetail.NONE
    )

    assert actual == expected


def test_get_in_system_by_id__route_not_found(monkeypatch):
    monkeypatch.setattr(routequeries, "get_in_system_by_id", lambda *args: None)

    with pytest.raises(exceptions.IdNotFoundError):
        routeservice.get_in_system_by_id(SYSTEM_ID, ROUTE_ONE_ID)


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
            ROUTE_ONE_PK: [(alert_1_model.active_periods[0], alert_1_model)]
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
        SYSTEM_ID, ROUTE_ONE_ID, None if return_alerts else views.AlertsDetail.NONE
    )

    assert expected == actual
