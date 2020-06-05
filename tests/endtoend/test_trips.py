import uuid

import pytest
import requests
from google.transit import gtfs_realtime_pb2 as gtfs


TRIP_ID = "trip_id"
ROUTE_ID = "A"
TRIP_INITIAL_TIMETABLE = {
    "1AS": 300,
    "1BS": 600,
    "1CS": 800,
    "1DS": 900,
    "1ES": 1800,
    "1FS": 2500,
}


# TODO: add current_time=4000 case when bug in import driver is fixed.
#  Or else just add a different test
@pytest.mark.parametrize("use_stop_sequences", [True, False])
@pytest.mark.parametrize("current_time", [0, 700])
@pytest.mark.parametrize(
    "stop_id_to_time_2",
    [
        # Basic case where the second update does nothing.
        TRIP_INITIAL_TIMETABLE,
        # Change the stop times - move time after update
        {"1AS": 300, "1BS": 800, "1CS": 850, "1DS": 900, "1ES": 1800, "1FS": 2500},
        # Change the stop times - move time before update
        {"1AS": 300, "1BS": 600, "1CS": 650, "1DS": 900, "1ES": 1800, "1FS": 2500},
        # Add a new stop
        {
            "1AS": 200,
            "1BS": 600,
            "1CS": 800,
            "1DS": 900,
            "1ES": 1800,
            "1FS": 2500,
            "1GS": 2600,
        },
        # Delete a stop from the end
        {"1AS": 200, "1BS": 600, "1CS": 800, "1DS": 900, "1ES": 1800},
        # Swap the ordering of the stops
        {
            "1AS": 300,
            "1BS": 600,
            "1CS": 800,
            "1DS": 900,
            "1ES": 1800,
            "1GS": 2500,
            "1FS": 3000,
        },
    ],
)
class TestTrip:
    def test_stop_view(
        self,
        install_system_1,
        system_id,
        transiter_host,
        source_server,
        stop_id_to_time_2,
        current_time,
        use_stop_sequences,
    ):
        __, realtime_feed_url = install_system_1(system_id)

        for stop_id_to_time, time_at_update in [
            (TRIP_INITIAL_TIMETABLE, 0),
            (stop_id_to_time_2, current_time),
        ]:
            source_server.put(
                realtime_feed_url,
                build_gtfs_rt_message(
                    time_at_update, stop_id_to_time, use_stop_sequences
                ).SerializeToString(),
            )
            requests.post(
                f"{transiter_host}/systems/{system_id}/feeds/GtfsRealtimeFeed?sync=true"
            )

        stop_id_to_stop_sequence = {
            stop_id: stop_sequence + 25
            for stop_sequence, stop_id in enumerate(stop_id_to_time_2.keys())
        }
        all_stop_ids = set(TRIP_INITIAL_TIMETABLE.keys()).union(
            stop_id_to_time_2.keys()
        )
        for stop_id in all_stop_ids:
            response = requests.get(
                f"{transiter_host}/systems/{system_id}/stops/{stop_id}"
            ).json()

            time = stop_id_to_time_2.get(stop_id)
            if time is None or time < current_time:
                assert [] == response["stop_times"]
                continue

            stop_time = response["stop_times"][0]

            assert stop_time["trip"]["id"] == TRIP_ID
            assert stop_time["trip"]["route"]["id"] == ROUTE_ID
            assert stop_time["arrival"]["time"] == time
            assert stop_time["departure"]["time"] == time + 15
            if use_stop_sequences:
                assert stop_time["stop_sequence"] == stop_id_to_stop_sequence[stop_id]

    def test_trip_view(
        self,
        install_system_1,
        system_id,
        transiter_host,
        source_server,
        stop_id_to_time_2,
        current_time,
        use_stop_sequences,
    ):
        __, realtime_feed_url = install_system_1(system_id)

        for stop_id_to_time, time_at_update in [
            (TRIP_INITIAL_TIMETABLE, 0),
            (stop_id_to_time_2, current_time),
        ]:
            source_server.put(
                realtime_feed_url,
                build_gtfs_rt_message(
                    time_at_update, stop_id_to_time, use_stop_sequences
                ).SerializeToString(),
            )
            requests.post(
                f"{transiter_host}/systems/{system_id}/feeds/GtfsRealtimeFeed?sync=true"
            )

        stop_ids_in_second_update = {
            stop_id
            for stop_id, time in stop_id_to_time_2.items()
            if time >= current_time
        }
        expected_past_stop_ids = []
        for stop_id, time in TRIP_INITIAL_TIMETABLE.items():
            if stop_id in stop_ids_in_second_update:
                break
            expected_past_stop_ids.append(stop_id)

        expected_future_stop_ids = [
            stop_id
            for stop_id, time in stop_id_to_time_2.items()
            if time >= current_time
        ]

        response = requests.get(
            f"{transiter_host}/systems/{system_id}/routes/{ROUTE_ID}/trips/{TRIP_ID}"
        ).json()
        actual_past_stop_ids = []
        actual_future_stop_ids = []
        for stop_time in response["stop_times"]:
            stop_id = stop_time["stop"]["id"]
            if stop_time["future"]:
                actual_future_stop_ids.append(stop_id)
            else:
                actual_past_stop_ids.append(stop_id)

        assert expected_past_stop_ids == actual_past_stop_ids
        assert expected_future_stop_ids == actual_future_stop_ids


def build_gtfs_rt_message(current_time, stop_id_to_time, use_stop_sequences):
    return gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0", timestamp=current_time),
        entity=[
            gtfs.FeedEntity(
                id="1",
                trip_update=gtfs.TripUpdate(
                    trip=gtfs.TripDescriptor(
                        trip_id=TRIP_ID, route_id=ROUTE_ID, direction_id=True
                    ),
                    stop_time_update=[
                        gtfs.TripUpdate.StopTimeUpdate(
                            arrival=gtfs.TripUpdate.StopTimeEvent(time=time),
                            departure=gtfs.TripUpdate.StopTimeEvent(time=time + 15),
                            stop_id=stop_id,
                            stop_sequence=stop_sequence + 25
                            if use_stop_sequences
                            else None,
                        )
                        for stop_sequence, (stop_id, time) in enumerate(
                            stop_id_to_time.items()
                        )
                        if time >= current_time
                    ],
                ),
            )
        ],
    )
