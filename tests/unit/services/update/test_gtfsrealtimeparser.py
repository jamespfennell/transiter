import datetime
import unittest
from unittest import mock

from google.protobuf.message import DecodeError
from google.transit import gtfs_realtime_pb2 as gtfs

from transiter import parse
from transiter.services.update import gtfsrealtimeparser
from ... import testutil

timestamp_to_datetime = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(
    ""
)._timestamp_to_datetime


class TestReadGtfsRealtime(testutil.TestCase(gtfsrealtimeparser)):
    RAW_CONTENT = "Some content"
    PARSED_CONTENT = "Transformed"

    def setUp(self):
        self.gtfs_feed = mock.MagicMock()

        self.gtfs_realtime_pb2 = self.mockImportedModule(
            gtfsrealtimeparser.gtfs_realtime_pb2
        )
        self.gtfs_realtime_pb2.FeedMessage.return_value = self.gtfs_feed

        self._read_protobuf_message = self.mockModuleAttribute("_read_protobuf_message")
        self._read_protobuf_message.return_value = self.PARSED_CONTENT

    def tearDown(self):
        self.gtfs_realtime_pb2.FeedMessage.assert_called_once_with()
        self.gtfs_feed.ParseFromString.assert_called_once_with(self.RAW_CONTENT)

    def test_read_gtfs_realtime_parse_error(self):
        """[GTFS Realtime Util] GTFS realtime parse error"""
        self.gtfs_feed.ParseFromString.side_effect = DecodeError

        self.assertRaises(
            DecodeError,
            lambda: gtfsrealtimeparser.read_gtfs_realtime(
                self.RAW_CONTENT, self.gtfs_realtime_pb2
            ),
        )

    def test_read_gtfs_realtime(self):
        """[GTFS Realtime Util] Read basic feed subtask scheduling"""
        actual_response = gtfsrealtimeparser.read_gtfs_realtime(
            self.RAW_CONTENT, self.gtfs_realtime_pb2
        )

        self.assertEqual(actual_response, self.PARSED_CONTENT)
        self._read_protobuf_message.assert_called_once_with(self.gtfs_feed)


class TestReadProtobufMessage(unittest.TestCase):
    GTFS_REALTIME_VERSION = "2.0"
    INCREMENTALITY = "FULL_DATASET"
    INCREMENTALITY_INT = gtfs.FeedHeader.Incrementality.Value(INCREMENTALITY)
    TIMESTAMP = 4
    ENTITY_1_ID = "1"
    ENTITY_2_ID = "2"
    CONGESTION_ONE = "STOP_AND_GO"
    CONGESTION_ONE_INT = gtfs.VehiclePosition.CongestionLevel.Value(CONGESTION_ONE)
    CONGESTION_TWO = "CONGESTION"
    CONGESTION_TWO_INT = gtfs.VehiclePosition.CongestionLevel.Value(CONGESTION_TWO)

    def test_read_protobuf_message(self):
        """[GTFS Realtime Util] Read protobuf message"""
        root = gtfs.FeedMessage()
        header = root.header
        header.gtfs_realtime_version = self.GTFS_REALTIME_VERSION
        header.incrementality = self.INCREMENTALITY_INT
        header.timestamp = self.TIMESTAMP
        entity_1 = root.entity.add()
        entity_1.id = self.ENTITY_1_ID
        entity_1.vehicle.congestion_level = self.CONGESTION_ONE_INT
        entity_2 = root.entity.add()
        entity_2.id = self.ENTITY_2_ID
        entity_2.vehicle.congestion_level = self.CONGESTION_TWO_INT

        expected_data = {
            "header": {
                "gtfs_realtime_version": self.GTFS_REALTIME_VERSION,
                "incrementality": self.INCREMENTALITY,
                "timestamp": self.TIMESTAMP,
            },
            "entity": [
                {
                    "id": self.ENTITY_1_ID,
                    "vehicle": {"congestion_level": self.CONGESTION_ONE},
                },
                {
                    "id": self.ENTITY_2_ID,
                    "vehicle": {"congestion_level": self.CONGESTION_TWO},
                },
            ],
        }

        actual_data = gtfsrealtimeparser._read_protobuf_message(root)

        self.assertDictEqual(actual_data, expected_data)


class TestParseAlerts(unittest.TestCase):

    ID = "1"
    CAUSE = parse.Alert.Cause.CONSTRUCTION
    EFFECT = parse.Alert.Effect.SIGNIFICANT_DELAYS
    HEADER = "2"
    DESCRIPTION = "3"

    def setUp(self):
        self.parser = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer("")

    def test_no_alerts(self):
        """[GTFS Realtime parser] Parse alerts, no alert data"""
        raw_data = {"entity": [{"id": self.ID, "vehicle": {}}]}

        self.assertEqual([], self.parser.build_alerts(raw_data))

    def test_no_alerts_ids(self):
        """[GTFS Realtime parser] Parse alerts, no alert id"""
        raw_data = {"entity": [{"alert": {}}]}

        self.assertEqual([], self.parser.build_alerts(raw_data))

    def test_base_case(self):
        """[GTFS Realtime parser] Parse alert base case"""

        raw_data = {
            "entity": [
                {
                    "id": self.ID,
                    "alert": {
                        "cause": self.CAUSE.name,
                        "effect": self.EFFECT.name,
                        "header_text": {"translation": [{"text": self.HEADER}]},
                        "description_text": {
                            "translation": [{"text": self.DESCRIPTION}]
                        },
                    },
                }
            ]
        }

        expected_alert = parse.Alert(
            id=self.ID,
            cause=self.CAUSE,
            effect=self.EFFECT,
            header=self.HEADER,
            description=self.DESCRIPTION,
        )

        self.assertEqual([expected_alert], self.parser.build_alerts(raw_data))

    def test_no_effect_or_cause(self):
        """[GTFS Realtime parser] Parse alert, no effect or cause"""

        raw_data = {
            "entity": [
                {
                    "id": self.ID,
                    "alert": {
                        "header_text": {"translation": [{"text": self.HEADER}]},
                        "description_text": {
                            "translation": [{"text": self.DESCRIPTION}]
                        },
                    },
                }
            ]
        }

        expected_alert = parse.Alert(
            id=self.ID,
            cause=parse.Alert.Cause.UNKNOWN_CAUSE,
            effect=parse.Alert.Effect.UNKNOWN_EFFECT,
            header=self.HEADER,
            description=self.DESCRIPTION,
        )

        self.assertEqual([expected_alert], self.parser.build_alerts(raw_data))


GTFS_REALTIME_VERSION = "2.0"
INCREMENTALITY = "FULL_DATASET"
INCREMENTALITY_INT = gtfs.FeedHeader.Incrementality.Value(INCREMENTALITY)
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
    transformer = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(raw_data)

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

    transformer = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(raw_data)
    transformer._group_trip_entities()

    assert expected_raw_entities == transformer._trip_id_to_raw_entities


def test_transform_trip_base_data():
    """[GTFS Realtime transformer] Transform trip base data"""
    transformer = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(None)
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
    transformer = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(None)
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
    transformer = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(None)
    trip = parse.Trip(id="trip", route_id="L", direction_id=True)
    transformer._trip_id_to_trip_model = {TRIP_ID: trip}
    transformer._trip_id_to_raw_entities = {TRIP_ID: {"trip": "Data"}}

    transformer._transform_trip_stop_events()

    assert [] == trip.stop_times


def test_update_stop_event_indices():
    """[GTFS Realtime transformer] Update stop event indices"""
    transformer = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(None)
    trip = parse.Trip(
        id="trip",
        route_id="L",
        direction_id=True,
        current_stop_sequence=15,
        stop_times=[parse.TripStopTime(stop_id="1"), parse.TripStopTime(stop_id="2")],
    )
    transformer._trip_id_to_trip_model = {TRIP_ID: trip}

    transformer._update_stop_event_indices()

    assert [15, 16] == [stu.stop_sequence for stu in trip.stop_times]


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
        stop_sequence=16,
        future=True,
        arrival_time=timestamp_to_datetime(STOP_ONE_ARR_TIMESTAMP),
        departure_time=timestamp_to_datetime(STOP_ONE_DEP_TIMESTAMP),
        track=None,
    )

    stu_2 = parse.TripStopTime(
        stop_id=STOP_TWO_ID,
        stop_sequence=17,
        future=True,
        arrival_time=timestamp_to_datetime(STOP_TWO_ARR_TIMESTAMP),
        departure_time=None,
        track=None,
    )

    trip.stop_times = [stu_1, stu_2]

    expected_feed_time = timestamp_to_datetime(FEED_UPDATE_TIMESTAMP)

    (
        actual_feed_time,
        actual_trips,
    ) = gtfsrealtimeparser.transform_to_transiter_structure(input)

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


def test_clean_all_good():
    """[GTFS static util] Trip cleaner - All good"""

    trip_cleaners = [mock.MagicMock() for __ in range(3)]
    for cleaner in trip_cleaners:
        cleaner.return_value = True
    stop_event_cleaners = [mock.MagicMock() for __ in range(3)]
    gtfs_cleaner = gtfsrealtimeparser.TripDataCleaner(
        trip_cleaners, stop_event_cleaners
    )

    trip = parse.Trip(
        id="trip",
        route_id="L",
        direction_id=True,
        stop_times=[parse.TripStopTime(stop_id="L03")],
    )

    clean_trips = gtfs_cleaner.clean([trip])

    assert [trip] == clean_trips

    for cleaner in trip_cleaners:
        cleaner.assert_called_once_with(trip)
    for cleaner in stop_event_cleaners:
        cleaner.assert_called_once_with(trip.stop_times[0])


def test_clean_buggy_trip():
    """[GTFS static util] Trip cleaner - Buggy trip"""

    trip_cleaners = [mock.MagicMock() for __ in range(3)]
    for cleaner in trip_cleaners:
        cleaner.return_value = True
    trip_cleaners[1].return_value = False
    stop_event_cleaners = [mock.MagicMock() for __ in range(3)]
    gtfs_cleaner = gtfsrealtimeparser.TripDataCleaner(
        trip_cleaners, stop_event_cleaners
    )

    trip = parse.Trip(
        id="trip",
        route_id="L",
        direction_id=True,
        stop_times=[parse.TripStopTime(stop_id="L03")],
    )

    clean_trips = gtfs_cleaner.clean([trip])

    assert [] == clean_trips
    trip_cleaners[0].assert_called_once_with(trip)
    trip_cleaners[1].assert_called_once_with(trip)
    trip_cleaners[2].assert_not_called()
    for cleaner in stop_event_cleaners:
        cleaner.assert_not_called()


def test_transform_trip_stop_events():
    """[GTFS Realtime transformer] Transform trip stop events"""

    transformer = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(None)
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
