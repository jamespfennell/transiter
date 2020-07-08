import datetime

import pytest

from transiter.db import models


@pytest.fixture
def trip_1(
    add_model, route_1_1, stop_1_1, stop_1_2, stop_1_3, stop_1_4, feed_1_1_update_1
):
    stop_times = [
        models.TripStopTime(
            arrival_time=datetime.datetime(2018, 11, 2, 10, 0, 0),
            stop=stop_1_1,
            stop_sequence=1,
        ),
        models.TripStopTime(
            arrival_time=datetime.datetime(2018, 11, 2, 10, 1, 0),
            stop=stop_1_2,
            stop_sequence=2,
        ),
        models.TripStopTime(
            arrival_time=datetime.datetime(2018, 11, 2, 10, 2, 0),
            stop=stop_1_3,
            stop_sequence=3,
        ),
        models.TripStopTime(
            arrival_time=datetime.datetime(2018, 11, 2, 10, 3, 0),
            stop=stop_1_4,
            stop_sequence=4,
        ),
    ]
    return add_model(
        models.Trip(
            pk=401,
            id="402",
            route=route_1_1,
            stop_times=stop_times,
            current_stop_sequence=1,
            source=feed_1_1_update_1,
        )
    )


@pytest.fixture
def trip_2(add_model, route_1_1, stop_1_1, stop_1_2, stop_1_4, feed_1_1_update_1):
    stop_times = [
        models.TripStopTime(
            arrival_time=datetime.datetime(2018, 11, 2, 11, 0, 0),
            stop=stop_1_1,
            stop_sequence=1,
        ),
        models.TripStopTime(
            arrival_time=datetime.datetime(2018, 11, 2, 11, 1, 0),
            stop=stop_1_2,
            stop_sequence=2,
        ),
        models.TripStopTime(
            arrival_time=datetime.datetime(2018, 11, 2, 11, 3, 0),
            stop=stop_1_4,
            stop_sequence=3,
        ),
    ]
    return add_model(
        models.Trip(
            pk=403,
            id="404",
            route=route_1_1,
            stop_times=stop_times,
            current_stop_sequence=1,
            source=feed_1_1_update_1,
        )
    )


@pytest.fixture
def trip_3(add_model, route_1_1, stop_1_1, stop_1_4, feed_1_1_update_1):
    stop_times = [
        models.TripStopTime(
            arrival_time=datetime.datetime(2018, 11, 2, 12, 0, 0),
            stop=stop_1_1,
            stop_sequence=1,
        ),
        models.TripStopTime(
            arrival_time=datetime.datetime(2018, 11, 2, 12, 3, 0),
            stop=stop_1_4,
            stop_sequence=3,
        ),
    ]
    return add_model(
        models.Trip(
            pk=404,
            id="406",
            route=route_1_1,
            stop_times=stop_times,
            current_stop_sequence=3,
            source=feed_1_1_update_1,
        )
    )
