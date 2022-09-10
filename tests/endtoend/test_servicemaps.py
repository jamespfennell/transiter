import requests

from . import gtfsrealtimegenerator

# TODO: stop using this module ^
#  Also break up these tests if reasonable


def test_service_maps(system_id, install_system_1, transiter_host, source_server):
    __, realtime_feed_url = install_system_1(system_id)

    # (1) Regular case
    trip_1_stops = {
        "1AS": 300,
        "1ES": 1800,
        "1FS": 2500,
    }
    trip_2_stops = {
        "1AS": 300,
        "1BS": 600,
        "1CS": 800,
        "1DS": 900,
        "1ES": 1800,
    }
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
        0,
        [
            gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0),
            gtfsrealtimegenerator.FeedTrip("trip_2", "A", trip_2_stops, 0),
        ],
    )
    _perform_service_map_test(
        system_id,
        transiter_host,
        source_server,
        realtime_feed_url,
        feed_1,
        ["1A", "1B", "1C", "1D", "1E", "1F"],
        ["trip_1", "trip_2"],
    )

    # (2) Old trips + new trips give an invalid map, but the update still happens
    # because old trips shouldn't count.
    trip_3_stops = {
        "1FS": 250,
        "1ES": 1800,
        "1AS": 3000,
    }
    trip_4_stops = {
        "1ES": 100,
        "1DS": 900,
        "1CS": 8000,
        "1BS": 60000,
        "1AS": 300000,
    }
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
        0,
        [
            gtfsrealtimegenerator.FeedTrip("trip_3", "A", trip_3_stops, 0),
            gtfsrealtimegenerator.FeedTrip("trip_4", "A", trip_4_stops, 0),
        ],
    )
    _perform_service_map_test(
        system_id,
        transiter_host,
        source_server,
        realtime_feed_url,
        feed_1,
        list(reversed(["1A", "1B", "1C", "1D", "1E", "1F"])),
        ["trip_3", "trip_4"],
    )

    # (3) With this update the map is now invalid so should not be updated, but the
    # trips are still updated successfully.
    trip_5_stops = {
        "1AS": 250,
        "1ES": 1800,
        "1FS": 3000,
    }
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
        0,
        [
            gtfsrealtimegenerator.FeedTrip("trip_3", "A", trip_3_stops, 100),
            gtfsrealtimegenerator.FeedTrip("trip_4", "A", trip_4_stops, 100),
            gtfsrealtimegenerator.FeedTrip("trip_5", "A", trip_5_stops, 0),
        ],
    )
    _perform_service_map_test(
        system_id,
        transiter_host,
        source_server,
        realtime_feed_url,
        feed_1,
        list(reversed(["1A", "1B", "1C", "1D", "1E", "1F"])),
        ["trip_3", "trip_4", "trip_5"],
    )

    # (4) Valid map again
    trip_1_stops = {
        "1AS": 300,
        "1ES": 1800,
        "1FS": 2500,
    }
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
        0,
        [
            gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0),
        ],
    )
    _perform_service_map_test(
        system_id,
        transiter_host,
        source_server,
        realtime_feed_url,
        feed_1,
        ["1A", "1E", "1F"],
        ["trip_1"],
    )

    # (5) No more trips, service map is deleted.
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
        0,
        [],
    )
    _perform_service_map_test(
        system_id,
        transiter_host,
        source_server,
        realtime_feed_url,
        feed_1,
        [],
        [],
    )


def _perform_service_map_test(
    system_id,
    transiter_host,
    source_server,
    realtime_feed_url,
    feed,
    expected_map_stop_ids,
    expected_trip_ids,
):
    source_server.put(realtime_feed_url, feed.build_feed())
    requests.post(
        transiter_host
        + "/admin/systems/"
        + system_id
        + "/feeds/GtfsRealtimeFeed?sync=true"
    ).json()

    route_data = requests.get(
        transiter_host + "/systems/" + system_id + "/routes/A"
    ).json()
    stop_ids = None
    for service_map in route_data["serviceMaps"]:
        print(service_map)
        if service_map["configId"] != "realtime":
            continue
        stop_ids = [stop["id"] for stop in service_map["stops"]]
    assert expected_map_stop_ids == stop_ids

    trips_in_route_data = requests.get(
        transiter_host + "/systems/" + system_id + "/routes/A/trips"
    ).json()["trips"]
    trip_ids = set(trip["id"] for trip in trips_in_route_data)
    assert set(expected_trip_ids) == trip_ids
