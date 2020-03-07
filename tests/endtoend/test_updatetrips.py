import requests

from . import gtfsrealtimegenerator


def test_update_trips(install_system_1, transiter_host, source_server):

    __, realtime_feed_url = install_system_1("test_update_trips")

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
        0, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
    )
    feed_2 = gtfsrealtimegenerator.GtfsRealtimeFeed(
        850, [gtfsrealtimegenerator.FeedTrip("trip_1", "A", trip_1_stops, 0)]
    )
    _perform_feed_update_trip_test(
        transiter_host, source_server, realtime_feed_url, [feed_1, feed_2]
    )


def _perform_feed_update_trip_test(
    transiter_host, source_server, realtime_feed_url, feeds
):
    for feed in feeds:
        source_server.put(realtime_feed_url, feed.build_feed())
        requests.post(
            transiter_host
            + "/systems/test_update_trips/feeds/GtfsRealtimeFeed?sync=true"
        )

    all_sss = []
    all_trips = set()
    all_trip_data = []
    for feed in feeds:
        (stop_sequences, trip_data) = feed.trip_data()
        all_sss.append(stop_sequences)
        all_trip_data.append(trip_data)
        all_trips.update(stop_sequences.keys())

    trip_to_expected_data = {trip_id: [] for trip_id in all_trips}
    trip_to_num_passed = {trip_id: 0 for trip_id in all_trips}
    for index, trip_data in enumerate(all_trip_data):
        for trip_id in all_trips:
            if trip_id not in trip_data:
                trip_to_expected_data[trip_id] = []
                trip_to_num_passed[trip_id] = 0
                continue
            current_stop_sequence = all_sss[index][trip_id]
            diff = len(trip_to_expected_data[trip_id]) - current_stop_sequence
            if diff < 0:
                trip_to_expected_data[trip_id] += [None] * (-diff)
            else:
                trip_to_expected_data[trip_id] = trip_to_expected_data[trip_id][
                    :current_stop_sequence
                ]

            trip_to_num_passed[trip_id] = len(trip_to_expected_data[trip_id])

            future_stops = [stop["stop_id"] for stop in trip_data[trip_id]]
            trip_to_expected_data[trip_id] += future_stops

    for trip_id in all_trips:

        expected_stop_list = []
        num_passed = trip_to_num_passed[trip_id]
        for index, stop_data in enumerate(trip_to_expected_data[trip_id]):
            if stop_data is None:
                continue
            expected_stop_list.append((stop_data, index >= num_passed))

        actual_data = requests.get(
            transiter_host
            + "/systems/test_update_trips/routes/A/trips/{}".format(trip_id)
        ).json()

        actual_stop_list = []
        for stop_data in actual_data["stop_time_updates"]:
            actual_stop_list.append((stop_data["stop"]["id"], stop_data["future"]))

        assert expected_stop_list == actual_stop_list
