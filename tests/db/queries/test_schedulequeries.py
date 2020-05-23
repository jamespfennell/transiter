import datetime

import pytest

from transiter.db import models
from transiter.db.queries import schedulequeries


@pytest.fixture
def scheduled_service_1(add_model, system_1, feed_1_1):
    feed_update = add_model(models.FeedUpdate(feed=feed_1_1))
    return add_model(
        models.ScheduledService(pk=811, id="812", system=system_1, source=feed_update)
    )


@pytest.fixture
def scheduled_trip_1_1(
    add_model, scheduled_service_1, route_1_1, stop_1_1, stop_1_2, stop_1_4
):
    stop_times = [
        models.ScheduledTripStopTime(
            stop_sequence=0, stop=stop_1_1, departure_time=datetime.time(11, 0, 0)
        ),
        models.ScheduledTripStopTime(
            stop_sequence=1, stop=stop_1_2, departure_time=datetime.time(11, 10, 0)
        ),
        models.ScheduledTripStopTime(
            stop_sequence=2, stop=stop_1_4, departure_time=datetime.time(11, 20, 0)
        ),
    ]
    return add_model(
        models.ScheduledTrip(
            pk=801,
            id="802",
            service=scheduled_service_1,
            route=route_1_1,
            stop_times=stop_times,
        )
    )


@pytest.fixture
def scheduled_service_2(add_model, system_2):
    return add_model(models.ScheduledService(pk=813, id="814", system=system_2))


@pytest.fixture
def scheduled_trip_2_1(
    add_model, scheduled_service_2, route_2_1, stop_2_1,
):
    stop_times = [
        models.ScheduledTripStopTime(
            stop_sequence=0, stop=stop_2_1, departure_time=datetime.time(11, 0, 0)
        ),
    ]
    return add_model(
        models.ScheduledTrip(
            pk=803,
            id="804",
            service=scheduled_service_2,
            route=route_2_1,
            stop_times=stop_times,
        )
    )


def test_get_scheduled_trip_pk_to_path_in_system(system_1, scheduled_trip_1_1):
    expected = {
        scheduled_trip_1_1.pk: [
            stop_time.stop.pk for stop_time in scheduled_trip_1_1.stop_times
        ]
    }

    actual = schedulequeries.get_scheduled_trip_pk_to_path_in_system(system_1.pk)

    assert expected == actual


def test_get_scheduled_trip_pk_to_path_in_system__no_trips(system_1):
    expected = {}

    actual = schedulequeries.get_scheduled_trip_pk_to_path_in_system(system_1.pk)

    assert expected == actual


def test_list_scheduled_trips_with_times_in_system(system_1, scheduled_trip_1_1):
    expected = [
        (
            scheduled_trip_1_1,
            scheduled_trip_1_1.stop_times[0].departure_time,
            scheduled_trip_1_1.stop_times[-1].departure_time,
        )
    ]

    actual = schedulequeries.list_scheduled_trips_with_times_in_system(system_1.pk)

    assert expected == actual


def test_list_scheduled_trips_with_times_in_system__no_trips(system_1):
    expected = []

    actual = schedulequeries.list_scheduled_trips_with_times_in_system(system_1.pk)

    assert expected == actual


def test_get_trip_id_to_pk_map_by_feed_pk(feed_1_1, scheduled_trip_1_1):
    expected = {scheduled_trip_1_1.id: scheduled_trip_1_1.pk}

    actual = schedulequeries.get_trip_id_to_pk_map_by_feed_pk(feed_1_1.pk)

    assert expected == actual


def test_get_trip_id_to_pk_map_by_feed_pk__no_trips(feed_1_1, scheduled_service_1):
    expected = {}

    actual = schedulequeries.get_trip_id_to_pk_map_by_feed_pk(feed_1_1.pk)

    assert expected == actual


def test_list_trips_by_system_pk_and_trip_ids(system_1, scheduled_trip_1_1):
    assert [scheduled_trip_1_1] == schedulequeries.list_trips_by_system_pk_and_trip_ids(
        system_1.pk, [scheduled_trip_1_1.id, "unknown_id"]
    )


def test_list_trips_by_system_pk_and_trip_ids__no_ids_provided(
    system_1, scheduled_trip_1_1
):
    assert [] == schedulequeries.list_trips_by_system_pk_and_trip_ids(system_1.pk, [])
