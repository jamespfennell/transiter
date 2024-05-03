from . import gtfsrealtimegenerator

# TODO: stop using this module ^
from . import client


def test_realtime(system_id, install_system_1, transiter_client, source_server):
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
    _check_realtime_service_maps(
        system_id,
        transiter_client,
        source_server,
        realtime_feed_url,
        feed_1,
        ["1A", "1B", "1C", "1D", "1E", "1F"],
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
    _check_realtime_service_maps(
        system_id,
        transiter_client,
        source_server,
        realtime_feed_url,
        feed_1,
        list(reversed(["1A", "1B", "1C", "1D", "1E", "1F"])),
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
    _check_realtime_service_maps(
        system_id,
        transiter_client,
        source_server,
        realtime_feed_url,
        feed_1,
        list(reversed(["1A", "1B", "1C", "1D", "1E", "1F"])),
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
    _check_realtime_service_maps(
        system_id,
        transiter_client,
        source_server,
        realtime_feed_url,
        feed_1,
        ["1A", "1E", "1F"],
    )

    # (5) No more trips, service map is deleted.
    feed_1 = gtfsrealtimegenerator.GtfsRealtimeFeed(
        0,
        [],
    )
    _check_realtime_service_maps(
        system_id,
        transiter_client,
        source_server,
        realtime_feed_url,
        feed_1,
        [],
    )


def _check_realtime_service_maps(
    system_id,
    transiter_client: client.TransiterClient,
    source_server,
    realtime_feed_url,
    feed,
    want_stop_ids,
):
    source_server.put(realtime_feed_url, feed.build_feed())
    transiter_client.perform_feed_update(system_id, "GtfsRealtimeFeed")

    # (1) validate the service map appears in the route endpoints
    route = transiter_client.get_route(system_id, "A")
    want_stops = [client.StopReference(id=stop_id) for stop_id in want_stop_ids]
    got_stops = []
    for service_map in route.serviceMaps:
        if service_map.configId != "realtime":
            continue
        got_stops = service_map.stops
        break
    assert got_stops == want_stops

    # (2) validate the service map appears in the stop endpoints
    want_stop_ids = set(want_stop_ids)
    for stop in transiter_client.list_stops(system_id).stops:
        want_routes = []
        if stop.id in want_stop_ids:
            want_routes = [client.RouteReference(id="A")]
        want_service_map = client.ServiceMapAtStop(
            configId="realtime",
            routes=want_routes,
        )

        got_routes = []
        for service_map in stop.serviceMaps:
            if service_map.configId != "realtime":
                continue
            got_routes = service_map.routes
            break
        got_service_map = client.ServiceMapAtStop(
            configId="realtime",
            routes=got_routes,
        )

        assert got_service_map == want_service_map
