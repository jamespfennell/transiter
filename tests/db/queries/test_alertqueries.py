import datetime
import typing

import pytest

from transiter.db import models
from transiter.db.queries import alertqueries

ALERT_ID_1 = "1"
ALERT_ID_2 = "2"
TIME_1 = datetime.datetime.utcfromtimestamp(1000)
TIME_2 = datetime.datetime.utcfromtimestamp(2000)
TIME_3 = datetime.datetime.utcfromtimestamp(3000)


@pytest.mark.parametrize(
    "model_type,query_function",
    [
        [models.Route, alertqueries.get_route_pk_to_active_alerts],
        [models.Stop, alertqueries.get_stop_pk_to_active_alerts],
    ],
)
def test_list_alerts__empty_list(
    add_model, system_1, model_type, query_function: typing.Callable, feed_1_1_update_1
):
    alert = add_model(
        models.Alert(
            id=ALERT_ID_1,
            system_pk=system_1.pk,
            active_periods=[models.AlertActivePeriod(starts_at=TIME_1, ends_at=TIME_3)],
            source=feed_1_1_update_1,
        )
    )

    result = query_function([], current_time=TIME_2)

    assert {} == result


@pytest.mark.parametrize("load_messages", [True, False])
@pytest.mark.parametrize(
    "model_type,query_function",
    [
        [models.Route, alertqueries.get_route_pk_to_active_alerts],
        [models.Stop, alertqueries.get_stop_pk_to_active_alerts],
        [models.Agency, alertqueries.get_agency_pk_to_active_alerts],
        [models.Trip, alertqueries.get_trip_pk_to_active_alerts],
    ],
)
@pytest.mark.parametrize(
    "alert_start,alert_end,current_time,expect_result",
    [
        [None, TIME_3, TIME_2, True],
        [TIME_1, None, TIME_2, True],
        [TIME_1, TIME_3, TIME_1, True],
        [TIME_1, TIME_3, TIME_2, True],
        [TIME_1, TIME_3, TIME_3, True],
        [TIME_1, TIME_2, TIME_3, False],
        [TIME_2, TIME_3, TIME_1, False],
        [TIME_2, None, TIME_1, False],
        [None, TIME_2, TIME_3, False],
    ],
)
def test_list_alerts__base(
    add_model,
    system_1,
    route_1_1,
    route_1_2,
    stop_1_1,
    stop_1_2,
    trip_1,
    trip_2,
    feed_1_1_update_1,
    agency_1_1,
    alert_start,
    alert_end,
    current_time,
    expect_result,
    model_type,
    query_function: typing.Callable,
    load_messages,
):
    alert = add_model(
        models.Alert(
            id=ALERT_ID_1,
            system_pk=system_1.pk,
            active_periods=[
                models.AlertActivePeriod(starts_at=alert_start, ends_at=alert_end)
            ],
            source=feed_1_1_update_1,
        )
    )
    alert_2 = add_model(
        models.Alert(
            id=ALERT_ID_2,
            system_pk=system_1.pk,
            active_periods=[
                models.AlertActivePeriod(starts_at=alert_start, ends_at=alert_end)
            ],
            source=feed_1_1_update_1,
        )
    )
    if model_type == models.Route:
        pk = route_1_1.pk
        alert.routes = [route_1_1]
        alert_2.routes = [route_1_2]
    elif model_type == models.Stop:
        pk = stop_1_1.pk
        alert.stops = [stop_1_1]
        alert_2.stops = [stop_1_2]
    elif model_type == models.Agency:
        pk = agency_1_1.pk
        alert.agencies = [agency_1_1]
    elif model_type == models.Trip:
        pk = trip_1.pk
        alert.trips = [trip_1]
        alert_2.trips = [trip_2]
    else:
        assert False

    result = query_function(
        [pk], current_time=current_time, load_messages=load_messages
    )

    if expect_result:
        assert {pk: [(alert.active_periods[0], alert)]} == result
    else:
        assert {pk: []} == result


@pytest.mark.parametrize(
    "model_type,query_function",
    [
        [models.Route, alertqueries.get_route_pk_to_active_alerts],
        [models.Stop, alertqueries.get_stop_pk_to_active_alerts],
    ],
)
def test_list_alerts__de_duplicate_active_periods(
    add_model,
    system_1,
    route_1_1,
    stop_1_1,
    feed_1_1_update_1,
    model_type,
    query_function: typing.Callable,
):
    alert = add_model(
        models.Alert(
            id=ALERT_ID_1,
            system_pk=system_1.pk,
            active_periods=[
                models.AlertActivePeriod(starts_at=TIME_1, ends_at=TIME_3),
                models.AlertActivePeriod(starts_at=TIME_1, ends_at=TIME_3),
            ],
            source=feed_1_1_update_1,
        )
    )
    if model_type == models.Route:
        pk = route_1_1.pk
        alert.routes = [route_1_1]
    elif model_type == models.Stop:
        pk = stop_1_1.pk
        alert.stops = [stop_1_1]
    else:
        assert False

    result = query_function([pk], current_time=TIME_2)

    assert [alert] == [alert for _, alert in result[pk]]
