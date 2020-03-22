import pytest
import requests

from . import gtfsrealtimegenerator


# TODO: break these up into different tests
#  add trip, change times, add extra stop,
#  remove a stop, put some in the past, change stops


@pytest.mark.parametrize("num_steps", [6])
def test_update_stops(install_system_1, transiter_host, source_server, num_steps):

    __, realtime_feed_url = install_system_1("test_update_stops")

    # (1)
    trip_1_stops = {
        "1AS": 300,
        "1BS": 600,
        "1CS": 800,
        "1DS": 900,
        "1ES": 1800,
        "1FS": 2500,
    }
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
        0, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
    )
    _perform_feed_update_stop_test(
        transiter_host, source_server, realtime_feed_url, feed_1
    )
    if num_steps <= 1:
        return

    # (2) Change the stop times
    trip_1_stops = {
        "1AS": 200,
        "1BS": 600,
        "1CS": 800,
        "1DS": 900,
        "1ES": 1800,
        "1FS": 2500,
    }
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
        0, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
    )
    _perform_feed_update_stop_test(
        transiter_host, source_server, realtime_feed_url, feed_1
    )
    if num_steps <= 2:
        return

    # (3) Add a new stop
    trip_1_stops = {
        "1AS": 200,
        "1BS": 600,
        "1CS": 800,
        "1DS": 900,
        "1ES": 1800,
        "1FS": 2500,
        "1GS": 2600,
    }
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
        0, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
    )
    _perform_feed_update_stop_test(
        transiter_host, source_server, realtime_feed_url, feed_1
    )
    if num_steps <= 3:
        return

    # (4) Delete a stop from the end
    trip_1_stops = {"1AS": 200, "1BS": 600, "1CS": 800, "1DS": 900, "1ES": 1800}

    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
        300, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
    )
    _perform_feed_update_stop_test(
        transiter_host, source_server, realtime_feed_url, feed_1
    )
    if num_steps <= 4:
        return

    # (5) Add the stop back in ... probably don't need this case?
    trip_1_stops = {
        "1AS": 300,
        "1BS": 600,
        "1CS": 800,
        "1DS": 900,
        "1ES": 1800,
        "1FS": 2500,
        "1GS": 3000,
    }
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
        850, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
    )
    _perform_feed_update_stop_test(
        transiter_host, source_server, realtime_feed_url, feed_1
    )
    if num_steps <= 5:
        return

    # (6) Swap the ordering of the stops
    trip_1_stops = {
        "1AS": 300,
        "1BS": 600,
        "1CS": 800,
        "1DS": 900,
        "1ES": 1800,
        "1GS": 2500,
        "1FS": 3000,
    }
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
        850, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
    )
    _perform_feed_update_stop_test(
        transiter_host, source_server, realtime_feed_url, feed_1
    )


def _perform_feed_update_stop_test(
    transiter_host, source_server, realtime_feed_url, feed_1
):
    source_server.put(realtime_feed_url, feed_1.build_feed())

    requests.post(
        transiter_host + "/systems/test_update_stops/feeds/GtfsRealtimeFeed?sync=true"
    )

    all_stop_data = feed_1.stop_data()
    for stop_id, stop_data in all_stop_data.items():
        actual_stop_data = []
        response = requests.get(
            transiter_host + "/systems/test_update_stops/stops/{}".format(stop_id)
        ).json()
        for stu in response["stop_times"]:
            actual_stop_data.append(
                {
                    "trip_id": stu["trip"]["id"],
                    "route_id": stu["trip"]["route"]["id"],
                    "arrival_time": stu["arrival"]["time"],
                    "departure_time": stu["departure"]["time"],
                }
            )
        assert stop_data == actual_stop_data

    prev_stop_ids = set(all_stop_data.keys())
    for stop_id in ["1AS", "1BS", "1CS", "1DS", "1ES", "1FS", "1GS"]:
        if stop_id in prev_stop_ids:
            continue
        response = requests.get(
            transiter_host + "/systems/test_update_stops/stops/{}".format(stop_id)
        ).json()
        assert [] == response["stop_times"]
