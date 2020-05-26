import datetime
import itertools

import pytest
import pytz
from google.transit import gtfs_realtime_pb2 as library_gtfs_rt_pb2

from transiter import parse
from transiter.parse import gtfsrealtime
from transiter.parse import transiter_gtfs_rt_pb2

timestamp_to_datetime = gtfsrealtime._GtfsRealtimeToTransiterTransformer(
    ""
)._timestamp_to_datetime

RAW_CONTENT = "Some content"
PARSED_CONTENT = "Transformed"


ALERT_ID = "alert_id"
LANGUAGE = "ie-ga"
URL = "url"
HEADER = "header"
DESCRIPTION = "description"
TIME_1 = datetime.datetime.utcfromtimestamp(3000).replace(tzinfo=pytz.UTC)
TIME_2 = datetime.datetime.utcfromtimestamp(60000).replace(tzinfo=pytz.UTC)
TRIP_ID = "trip_id"
ROUTE_ID = "route_id"
STOP_ID = "stop_id"
AGENCY_ID = "agency_id"


def build_test_parse_alerts_params(gtfs):
    return [
        [
            gtfs.Alert(cause=parse.Alert.Cause.DEMONSTRATION.value),
            parse.Alert(
                id=ALERT_ID,
                cause=parse.Alert.Cause.DEMONSTRATION,
                effect=parse.Alert.Effect.UNKNOWN_EFFECT,
            ),
        ],
        [
            gtfs.Alert(effect=parse.Alert.Effect.ADDITIONAL_SERVICE.value),
            parse.Alert(
                id=ALERT_ID,
                cause=parse.Alert.Cause.UNKNOWN_CAUSE,
                effect=parse.Alert.Effect.ADDITIONAL_SERVICE,
            ),
        ],
        *[
            [
                gtfs.Alert(
                    header_text=gtfs.TranslatedString(
                        translation=[
                            gtfs.TranslatedString.Translation(
                                text=HEADER, language=language
                            )
                        ]
                    ),
                    description_text=gtfs.TranslatedString(
                        translation=[
                            gtfs.TranslatedString.Translation(
                                text=DESCRIPTION, language=language
                            )
                        ]
                    ),
                    url=gtfs.TranslatedString(
                        translation=[
                            gtfs.TranslatedString.Translation(
                                text=URL, language=language
                            )
                        ]
                    ),
                ),
                parse.Alert(
                    id=ALERT_ID,
                    messages=[
                        parse.AlertMessage(
                            header=HEADER,
                            description=DESCRIPTION,
                            url=URL,
                            language=language,
                        )
                    ],
                ),
            ]
            for language in [LANGUAGE, None]
        ],
        [
            gtfs.Alert(
                active_period=[
                    gtfs.TimeRange(
                        start=int(TIME_1.timestamp()), end=int(TIME_2.timestamp())
                    )
                ]
            ),
            parse.Alert(
                id=ALERT_ID,
                active_periods=[
                    parse.AlertActivePeriod(starts_at=TIME_1, ends_at=TIME_2)
                ],
            ),
        ],
        [
            gtfs.Alert(
                informed_entity=[
                    gtfs.EntitySelector(
                        trip=gtfs.TripDescriptor(trip_id=TRIP_ID, route_id=ROUTE_ID)
                    )
                ]
            ),
            parse.Alert(id=ALERT_ID, trip_ids=[TRIP_ID]),
        ],
        [
            gtfs.Alert(
                informed_entity=[
                    gtfs.EntitySelector(trip=gtfs.TripDescriptor(route_id=ROUTE_ID))
                ]
            ),
            parse.Alert(id=ALERT_ID, route_ids=[ROUTE_ID]),
        ],
        [
            gtfs.Alert(informed_entity=[gtfs.EntitySelector(route_id=ROUTE_ID)]),
            parse.Alert(id=ALERT_ID, route_ids=[ROUTE_ID]),
        ],
        [
            gtfs.Alert(informed_entity=[gtfs.EntitySelector(agency_id=AGENCY_ID)]),
            parse.Alert(id=ALERT_ID, agency_ids=[AGENCY_ID]),
        ],
        [
            gtfs.Alert(informed_entity=[gtfs.EntitySelector(stop_id=STOP_ID)]),
            parse.Alert(id=ALERT_ID, stop_ids=[STOP_ID]),
        ],
    ]


@pytest.mark.parametrize(
    "input_alert,expected_alert,gtfs",
    itertools.chain.from_iterable(
        [
            (input_alert, expected_alert, gtfs_rt_pb2)
            for input_alert, expected_alert in build_test_parse_alerts_params(
                gtfs_rt_pb2
            )
        ]
        for gtfs_rt_pb2 in [transiter_gtfs_rt_pb2, library_gtfs_rt_pb2]
    ),
)
def test_parse_alerts(input_alert, expected_alert, gtfs):
    alert_message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[gtfs.FeedEntity(id=ALERT_ID, alert=input_alert)],
    )

    parser = gtfsrealtime.GtfsRealtimeParser()
    parser.load_content(alert_message.SerializeToString())
    actual_alerts = list(parser.get_alerts())

    assert [expected_alert] == actual_alerts


@pytest.mark.parametrize("gtfs", [transiter_gtfs_rt_pb2, library_gtfs_rt_pb2])
def test_parse_alerts__trip_ignored(gtfs):
    alert_message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[
            gtfs.FeedEntity(
                id=ALERT_ID,
                trip_update=gtfs.TripUpdate(trip=gtfs.TripDescriptor(trip_id=ALERT_ID)),
            )
        ],
    )

    parser = gtfsrealtime.GtfsRealtimeParser()
    parser.load_content(alert_message.SerializeToString())
    actual_alerts = list(parser.get_alerts())

    assert [] == actual_alerts


def test_parse_alerts__transiter_extension():
    gtfs = transiter_gtfs_rt_pb2

    alert_extension_key = gtfs.Alert._extensions_by_number[
        gtfsrealtime.TRANSITER_EXTENSION_ID
    ]

    input_alert = gtfs.Alert()
    additional_data = input_alert.Extensions[alert_extension_key]
    additional_data.created_at = int(TIME_1.timestamp())
    additional_data.updated_at = int(TIME_2.timestamp())
    additional_data.sort_order = 59
    alert_message = gtfs.FeedMessage(
        header=gtfs.FeedHeader(gtfs_realtime_version="2.0"),
        entity=[gtfs.FeedEntity(id=ALERT_ID, alert=input_alert)],
    )

    expected_alert = parse.Alert(
        id=ALERT_ID, created_at=TIME_1, updated_at=TIME_2, sort_order=59
    )

    parser = gtfsrealtime.GtfsRealtimeParser()
    parser.load_content(alert_message.SerializeToString())
    actual_alerts = list(parser.get_alerts())

    assert [expected_alert] == actual_alerts


GTFS_REALTIME_VERSION = "2.0"
INCREMENTALITY = "FULL_DATASET"
INCREMENTALITY_INT = 0
FEED_UPDATE_TIMESTAMP = 4
TRIP_UPDATE_TIMESTAMP = 5
STOP_ONE_ID = "Stop 1"
STOP_ONE_ARR_TIMESTAMP = 6
STOP_ONE_DEP_TIMESTAMP = 7
STOP_TWO_ID = "Stop 2"
STOP_TWO_ARR_TIMESTAMP = 8
ENTITY_1_ID = "1"
ENTITY_2_ID = "2"
TRIP_ID = "Trip 1"
ROUTE_ID = "L"
START_DATE = "19900326"
TRAIN_ID = "Train ID"
TRIP_DIRECTION = "North"
TRIP_DIRECTION_ID = True
CURRENT_STATUS = "Stopped"
CURRENT_STOP_SEQUENCE = 14


def test_transform_feed_metadata():
    """[GTFS Realtime transformer] Transform feed metadata"""
    raw_data = {
        "header": {"timestamp": FEED_UPDATE_TIMESTAMP, "other_field": "other value"},
        "other_field": "other value",
    }
    expected_transformed_metadata = {
        "timestamp": timestamp_to_datetime(FEED_UPDATE_TIMESTAMP)
    }
    transformer = gtfsrealtime._GtfsRealtimeToTransiterTransformer(raw_data)

    transformer._transform_feed_metadata()

    assert expected_transformed_metadata == transformer._transformed_metadata


def test_group_trip_entities():
    """[GTFS Realtime transformer] Group trip entities"""
    trip_dict = {"trip_id": TRIP_ID}
    entity_dict = {"trip": trip_dict}

    raw_data = {
        "entity": [
            {"trip_update": entity_dict},
            {"vehicle": entity_dict},
            {"unknown": "unknown"},
        ]
    }
    expected_raw_entities = {
        TRIP_ID: {
            "trip": trip_dict,
            "trip_update": entity_dict,
            "vehicle": entity_dict,
        }
    }

    transformer = gtfsrealtime._GtfsRealtimeToTransiterTransformer(raw_data)
    transformer._group_trip_entities()

    assert expected_raw_entities == transformer._trip_id_to_raw_entities


def test_transform_trip_base_data():
    """[GTFS Realtime transformer] Transform trip base data"""
    transformer = gtfsrealtime._GtfsRealtimeToTransiterTransformer(None)
    transformer._trip_id_to_raw_entities = {
        TRIP_ID: {
            "trip_update": {"vehicle": {"id": TRAIN_ID}},
            "trip": {
                "trip_id": TRIP_ID,
                "route_id": ROUTE_ID,
                "start_date": START_DATE,
                "direction_id": TRIP_DIRECTION_ID,
            },
        }
    }
    transformer._feed_time = FEED_UPDATE_TIMESTAMP

    trip = parse.Trip(
        id=TRIP_ID,
        route_id=ROUTE_ID,
        start_time=datetime.datetime(year=1990, month=3, day=26),
        train_id=TRAIN_ID,
        direction_id=TRIP_DIRECTION_ID,
        current_status=None,
        current_stop_sequence=0,
        updated_at=None,
    )

    expected_transformed_base_data = {TRIP_ID: trip}

    transformer._transform_trip_base_data()

    assert expected_transformed_base_data == transformer._trip_id_to_trip_model


def test_transform_trip_base_data_with_vehicle():
    """[GTFS Realtime transformer] Transform trip base data with vehicle"""
    transformer = gtfsrealtime._GtfsRealtimeToTransiterTransformer(None)
    transformer._trip_id_to_raw_entities = {
        TRIP_ID: {
            "trip_update": {"vehicle": {"id": TRAIN_ID}},
            "trip": {
                "trip_id": TRIP_ID,
                "route_id": ROUTE_ID,
                "start_date": START_DATE,
                "direction_id": TRIP_DIRECTION_ID,
            },
            "vehicle": {
                "timestamp": TRIP_UPDATE_TIMESTAMP,
                "current_status": "STOPPED_AT",
                "current_stop_sequence": CURRENT_STOP_SEQUENCE,
            },
        }
    }
    transformer._feed_time = FEED_UPDATE_TIMESTAMP

    trip = parse.Trip(
        id=TRIP_ID,
        route_id=ROUTE_ID,
        start_time=datetime.datetime(year=1990, month=3, day=26),
        train_id=TRAIN_ID,
        direction_id=TRIP_DIRECTION_ID,
        current_status=parse.Trip.Status.STOPPED_AT,
        current_stop_sequence=CURRENT_STOP_SEQUENCE,
        updated_at=timestamp_to_datetime(TRIP_UPDATE_TIMESTAMP),
    )
    expected_transformed_base_data = {TRIP_ID: trip}

    transformer._transform_trip_base_data()

    assert expected_transformed_base_data == transformer._trip_id_to_trip_model


def test_transform_trip_stop_events_short_circuit():
    """[GTFS Realtime transformer] Transform trip base data with no stops"""
    transformer = gtfsrealtime._GtfsRealtimeToTransiterTransformer(None)
    trip = parse.Trip(id="trip", route_id="L", direction_id=True)
    transformer._trip_id_to_trip_model = {TRIP_ID: trip}
    transformer._trip_id_to_raw_entities = {TRIP_ID: {"trip": "Data"}}

    transformer._transform_trip_stop_events()

    assert [] == trip.stop_times


def test_start_to_finish_parse():
    """[GTFS Realtime transformer] Full transformation test"""
    input = {
        "header": {
            "gtfs_realtime_version": GTFS_REALTIME_VERSION,
            "incrementality": INCREMENTALITY,
            "timestamp": FEED_UPDATE_TIMESTAMP,
        },
        "entity": [
            {
                "id": ENTITY_1_ID,
                "vehicle": {
                    "trip": {
                        "trip_id": "trip_id",
                        "start_date": "20180915",
                        "route_id": "4",
                    },
                    "current_stop_sequence": 16,
                    "current_status": "IN_TRANSIT_TO",
                    "timestamp": TRIP_UPDATE_TIMESTAMP,
                    "stop_id": "626S",
                },
            },
            {
                "id": ENTITY_2_ID,
                "trip_update": {
                    "trip": {
                        "trip_id": "trip_id",
                        "start_date": "20180915",
                        "route_id": "4",
                    },
                    "stop_time_update": [
                        {
                            "arrival": {"time": STOP_ONE_ARR_TIMESTAMP},
                            "departure": {"time": STOP_ONE_DEP_TIMESTAMP},
                            "stop_id": STOP_ONE_ID,
                        },
                        {
                            "arrival": {"time": STOP_TWO_ARR_TIMESTAMP},
                            "stop_id": STOP_TWO_ID,
                        },
                    ],
                },
            },
        ],
    }

    trip = parse.Trip(
        id="trip_id",
        train_id=None,
        route_id="4",
        start_time=datetime.datetime(year=2018, month=9, day=15),
        current_status=parse.Trip.Status.IN_TRANSIT_TO,
        current_stop_sequence=16,
        direction_id=None,
        updated_at=timestamp_to_datetime(TRIP_UPDATE_TIMESTAMP),
        current_stop_id="626S",
    )

    stu_1 = parse.TripStopTime(
        stop_id=STOP_ONE_ID,
        stop_sequence=None,
        future=True,
        arrival_time=timestamp_to_datetime(STOP_ONE_ARR_TIMESTAMP),
        departure_time=timestamp_to_datetime(STOP_ONE_DEP_TIMESTAMP),
        track=None,
    )

    stu_2 = parse.TripStopTime(
        stop_id=STOP_TWO_ID,
        stop_sequence=None,
        future=True,
        arrival_time=timestamp_to_datetime(STOP_TWO_ARR_TIMESTAMP),
        departure_time=None,
        track=None,
    )

    trip.stop_times = [stu_1, stu_2]

    expected_feed_time = timestamp_to_datetime(FEED_UPDATE_TIMESTAMP)

    (actual_feed_time, actual_trips,) = gtfsrealtime.transform_to_transiter_structure(
        input
    )

    assert actual_feed_time == expected_feed_time
    assert [trip] == actual_trips
    assert trip.stop_times == actual_trips[0].stop_times


def test_timestamp_to_datetime_edge_case_1():
    """[GTFS Realtime Util] Timestamp to datetime edge case 1"""
    actual = timestamp_to_datetime(None)

    assert actual is None


def test_timestamp_to_datetime_edge_case_2():
    """[GTFS Realtime Util] Timestamp to datetime edge case 2"""
    actual = timestamp_to_datetime(0)

    assert actual is None


def test_transform_trip_stop_events():
    """[GTFS Realtime transformer] Transform trip stop events"""

    transformer = gtfsrealtime._GtfsRealtimeToTransiterTransformer(None)
    trip = parse.Trip(id="trip", route_id="L", direction_id=True)
    trip.id = TRIP_ID
    transformer._trip_id_to_trip_model = {TRIP_ID: trip}
    transformer._trip_id_to_raw_entities = {
        TRIP_ID: {
            "trip": "Data",
            "trip_update": {
                "stop_time_update": [
                    {
                        "arrival": {"time": STOP_ONE_ARR_TIMESTAMP},
                        "departure": {"time": STOP_ONE_DEP_TIMESTAMP},
                        "stop_id": STOP_ONE_ID,
                    },
                    {
                        "arrival": {"time": STOP_TWO_ARR_TIMESTAMP},
                        "stop_id": STOP_TWO_ID,
                    },
                ]
            },
        }
    }

    stu_1 = parse.TripStopTime(
        stop_id=STOP_ONE_ID,
        arrival_time=timestamp_to_datetime(STOP_ONE_ARR_TIMESTAMP),
        departure_time=timestamp_to_datetime(STOP_ONE_DEP_TIMESTAMP),
        track=None,
    )

    stu_2 = parse.TripStopTime(
        stop_id=STOP_TWO_ID,
        arrival_time=timestamp_to_datetime(STOP_TWO_ARR_TIMESTAMP),
        departure_time=None,
        track=None,
    )

    transformer._transform_trip_stop_events()

    assert [stu_1, stu_2] == trip.stop_times
