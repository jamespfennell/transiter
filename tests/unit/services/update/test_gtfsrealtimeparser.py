import datetime
import unittest
from unittest import mock

from google.protobuf.message import DecodeError
from google.transit import gtfs_realtime_pb2 as gtfs

from transiter import models
from transiter.services.update import gtfsrealtimeparser
from ... import testutil


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
    CAUSE = models.Alert.Cause.CONSTRUCTION
    EFFECT = models.Alert.Effect.SIGNIFICANT_DELAYS
    HEADER = "2"

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
                    },
                }
            ]
        }

        expected_alert = models.Alert(
            id=self.ID, cause=self.CAUSE, effect=self.EFFECT, header=self.HEADER
        )

        self.assertEqual([expected_alert], self.parser.build_alerts(raw_data))

    def test_no_effect_or_cause(self):
        """[GTFS Realtime parser] Parse alert, no effect or cause"""

        raw_data = {
            "entity": [
                {
                    "id": self.ID,
                    "alert": {"header_text": {"translation": [{"text": self.HEADER}]}},
                }
            ]
        }

        expected_alert = models.Alert(
            id=self.ID,
            cause=models.Alert.Cause.UNKNOWN_CAUSE,
            effect=models.Alert.Effect.UNKNOWN_EFFECT,
            header=self.HEADER,
        )

        self.assertEqual([expected_alert], self.parser.build_alerts(raw_data))


class TestTransformGtfsRealtime(unittest.TestCase):
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

    def setUp(self):
        self.timestamp_to_datetime = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(
            ""
        )._timestamp_to_datetime

    def test_transform_feed_metadata(self):
        """[GTFS Realtime transformer] Transform feed metadata"""
        raw_data = {
            "header": {
                "timestamp": self.FEED_UPDATE_TIMESTAMP,
                "other_field": "other value",
            },
            "other_field": "other value",
        }
        expected_transformed_metadata = {
            "timestamp": self.timestamp_to_datetime(self.FEED_UPDATE_TIMESTAMP)
        }
        transformer = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(raw_data)

        transformer._transform_feed_metadata()

        self.assertDictEqual(
            expected_transformed_metadata, transformer._transformed_metadata
        )

    def test_group_trip_entities(self):
        """[GTFS Realtime transformer] Group trip entities"""
        trip_dict = {"trip_id": self.TRIP_ID}
        entity_dict = {"trip": trip_dict}

        raw_data = {
            "entity": [
                {"trip_update": entity_dict},
                {"vehicle": entity_dict},
                {"unknown": "unknown"},
            ]
        }
        expected_raw_entities = {
            self.TRIP_ID: {
                "trip": trip_dict,
                "trip_update": entity_dict,
                "vehicle": entity_dict,
            }
        }

        transformer = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(raw_data)
        transformer._group_trip_entities()

        self.assertDictEqual(
            expected_raw_entities, transformer._trip_id_to_raw_entities
        )

    def test_transform_trip_base_data(self):
        """[GTFS Realtime transformer] Transform trip base data"""
        transformer = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(None)
        transformer._trip_id_to_raw_entities = {
            self.TRIP_ID: {
                "trip": {
                    "trip_id": self.TRIP_ID,
                    "route_id": self.ROUTE_ID,
                    "start_date": self.START_DATE,
                    "train_id": self.TRAIN_ID,
                    "direction_id": self.TRIP_DIRECTION_ID,
                }
            }
        }
        transformer._feed_time = self.FEED_UPDATE_TIMESTAMP

        trip = models.Trip()
        trip.id = self.TRIP_ID
        trip.route_id = self.ROUTE_ID
        trip.start_time = datetime.datetime(year=1990, month=3, day=26)
        trip.train_id = self.TRAIN_ID
        trip.direction_id = self.TRIP_DIRECTION_ID
        trip.current_status = None
        trip.current_stop_sequence = 0
        trip.last_update_time = None
        trip.feed_update_time = None
        expected_transformed_base_data = {self.TRIP_ID: trip}

        transformer._transform_trip_base_data()
        # self.assertEqual(trip, transformer._trip_id_to_raw_entities[self.TRIP_ID])
        self.assertDictEqual(
            expected_transformed_base_data, transformer._trip_id_to_trip_model
        )

    def test_transform_trip_base_data_with_vehicle(self):
        """[GTFS Realtime transformer] Transform trip base data with vehicle"""
        transformer = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(None)
        transformer._trip_id_to_raw_entities = {
            self.TRIP_ID: {
                "trip": {
                    "trip_id": self.TRIP_ID,
                    "route_id": self.ROUTE_ID,
                    "start_date": self.START_DATE,
                    "train_id": self.TRAIN_ID,
                    "direction_id": self.TRIP_DIRECTION_ID,
                },
                "vehicle": {
                    "timestamp": self.TRIP_UPDATE_TIMESTAMP,
                    "current_status": "STOPPED_AT",
                    "current_stop_sequence": self.CURRENT_STOP_SEQUENCE,
                },
            }
        }
        transformer._feed_time = self.FEED_UPDATE_TIMESTAMP

        trip = models.Trip()
        trip.id = self.TRIP_ID
        trip.route_id = self.ROUTE_ID
        trip.start_time = datetime.datetime(year=1990, month=3, day=26)
        trip.train_id = self.TRAIN_ID
        trip.direction_id = self.TRIP_DIRECTION_ID
        trip.current_status = trip.TripStatus.STOPPED_AT
        trip.current_stop_sequence = self.CURRENT_STOP_SEQUENCE
        trip.last_update_time = self.timestamp_to_datetime(self.TRIP_UPDATE_TIMESTAMP)
        trip.feed_update_time = None
        expected_transformed_base_data = {self.TRIP_ID: trip}

        transformer._transform_trip_base_data()

        self.assertDictEqual(
            expected_transformed_base_data, transformer._trip_id_to_trip_model
        )

    def test_transform_trip_stop_events_short_circuit(self):
        """[GTFS Realtime transformer] Transform trip base data with no stops"""
        transformer = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(None)
        trip = models.Trip()
        transformer._trip_id_to_trip_model = {self.TRIP_ID: trip}
        transformer._trip_id_to_raw_entities = {self.TRIP_ID: {"trip": "Data"}}

        transformer._transform_trip_stop_events()

        self.assertEqual([], trip.stop_times)

    def test_transform_trip_stop_events(self):
        """[GTFS Realtime transformer] Transform trip stop events"""
        transformer = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(None)
        trip = models.Trip()
        transformer._trip_id_to_trip_model = {self.TRIP_ID: trip}
        transformer._trip_id_to_raw_entities = {
            self.TRIP_ID: {
                "trip": "Data",
                "trip_update": {
                    "stop_time_update": [
                        {
                            "arrival": {"time": self.STOP_ONE_ARR_TIMESTAMP},
                            "departure": {"time": self.STOP_ONE_DEP_TIMESTAMP},
                            "stop_id": self.STOP_ONE_ID,
                        },
                        {
                            "arrival": {"time": self.STOP_TWO_ARR_TIMESTAMP},
                            "stop_id": self.STOP_TWO_ID,
                        },
                    ]
                },
            }
        }

        stu_1 = models.TripStopTime()
        stu_1.stop_id = self.STOP_ONE_ID
        stu_1.arrival_time = self.timestamp_to_datetime(self.STOP_ONE_ARR_TIMESTAMP)
        stu_1.departure_time = self.timestamp_to_datetime(self.STOP_ONE_DEP_TIMESTAMP)
        stu_1.track: None

        stu_2 = models.TripStopTime()
        stu_2.stop_id = self.STOP_TWO_ID
        stu_2.arrival_time = self.timestamp_to_datetime(self.STOP_TWO_ARR_TIMESTAMP)
        stu_2.departure_time = None
        stu_2.track = None

        transformer._transform_trip_stop_events()

        self.maxDiff = None
        self.assertEqual([stu_1, stu_2], trip.stop_times)

    def test_update_stop_event_indices(self):
        """[GTFS Realtime transformer] Update stop event indices"""
        transformer = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(None)
        trip = models.Trip()
        trip.current_stop_sequence = 15
        trip.stop_times = [models.TripStopTime(), models.TripStopTime()]
        transformer._trip_id_to_trip_model = {self.TRIP_ID: trip}

        transformer._update_stop_event_indices()

        self.assertEqual([15, 16], [stu.stop_sequence for stu in trip.stop_times])

    def test_start_to_finish_parse(self):
        """[GTFS Realtime transformer] Full transformation test"""
        input = {
            "header": {
                "gtfs_realtime_version": self.GTFS_REALTIME_VERSION,
                "incrementality": self.INCREMENTALITY,
                "timestamp": self.FEED_UPDATE_TIMESTAMP,
            },
            "entity": [
                {
                    "id": self.ENTITY_1_ID,
                    "vehicle": {
                        "trip": {
                            "trip_id": "trip_id",
                            "start_date": "20180915",
                            "route_id": "4",
                        },
                        "current_stop_sequence": 16,
                        "current_status": "IN_TRANSIT_TO",
                        "timestamp": self.TRIP_UPDATE_TIMESTAMP,
                        "stop_id": "626S",
                    },
                },
                {
                    "id": self.ENTITY_2_ID,
                    "trip_update": {
                        "trip": {
                            "trip_id": "trip_id",
                            "start_date": "20180915",
                            "route_id": "4",
                        },
                        "stop_time_update": [
                            {
                                "arrival": {"time": self.STOP_ONE_ARR_TIMESTAMP},
                                "departure": {"time": self.STOP_ONE_DEP_TIMESTAMP},
                                "stop_id": self.STOP_ONE_ID,
                            },
                            {
                                "arrival": {"time": self.STOP_TWO_ARR_TIMESTAMP},
                                "stop_id": self.STOP_TWO_ID,
                            },
                        ],
                    },
                },
            ],
        }

        timestamp_to_datetime = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(
            ""
        )._timestamp_to_datetime
        trip = models.Trip()
        trip.id = "trip_id"
        trip.train_id = None
        trip.route_id = "4"
        trip.start_time = datetime.datetime(year=2018, month=9, day=15)
        trip.current_status = trip.TripStatus.IN_TRANSIT_TO
        trip.current_stop_sequence = 16
        trip.direction_id = None
        # trip.feed_update_time = self.timestamp_to_datetime(self.FEED_UPDATE_TIMESTAMP)
        trip.last_update_time = self.timestamp_to_datetime(self.TRIP_UPDATE_TIMESTAMP)

        stu_1 = models.TripStopTime()
        stu_1.stop_id = self.STOP_ONE_ID
        stu_1.stop_sequence = 17
        stu_1.arrival_time = self.timestamp_to_datetime(self.STOP_ONE_ARR_TIMESTAMP)
        stu_1.departure_time = self.timestamp_to_datetime(self.STOP_ONE_DEP_TIMESTAMP)
        stu_1.track = None

        stu_2 = models.TripStopTime()
        stu_2.stop_id = self.STOP_ONE_ID
        stu_2.stop_sequence = 18
        stu_1.arrival_time = self.timestamp_to_datetime(self.STOP_TWO_ARR_TIMESTAMP)
        stu_1.departure_time = None
        stu_2.track = None

        trip.stop_times.extend([stu_1, stu_2])

        expected_feed_time = timestamp_to_datetime(self.FEED_UPDATE_TIMESTAMP)

        (
            actual_feed_time,
            actual_trips,
        ) = gtfsrealtimeparser.transform_to_transiter_structure(input)

        self.maxDiff = None
        self.assertEqual(actual_feed_time, expected_feed_time)
        self.assertEqual([trip], actual_trips)

    def test_timestamp_to_datetime_edge_case_1(self):
        """[GTFS Realtime Util] Timestamp to datetime edge case 1"""
        actual = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(
            ""
        )._timestamp_to_datetime(None)
        self.assertEqual(None, actual)

    def test_timestamp_to_datetime_edge_case_2(self):
        """[GTFS Realtime Util] Timestamp to datetime edge case 2"""
        actual = gtfsrealtimeparser._GtfsRealtimeToTransiterTransformer(
            ""
        )._timestamp_to_datetime(0)
        self.assertEqual(None, actual)

    def test_clean_all_good(self):
        """[GTFS static util] Trip cleaner - All good"""

        trip_cleaners = [mock.MagicMock() for __ in range(3)]
        for cleaner in trip_cleaners:
            cleaner.return_value = True
        stop_event_cleaners = [mock.MagicMock() for __ in range(3)]
        gtfs_cleaner = gtfsrealtimeparser.TripDataCleaner(
            trip_cleaners, stop_event_cleaners
        )

        stop_event = models.TripStopTime()
        trip = models.Trip()
        trip.stop_times.append(stop_event)

        clean_trips = gtfs_cleaner.clean([trip])

        self.assertEqual([trip], clean_trips)
        for cleaner in trip_cleaners:
            cleaner.assert_called_once_with(trip)
        for cleaner in stop_event_cleaners:
            cleaner.assert_called_once_with(stop_event)

    def test_clean_buggy_trip(self):
        """[GTFS static util] Trip cleaner - Buggy trip"""

        trip_cleaners = [mock.MagicMock() for __ in range(3)]
        for cleaner in trip_cleaners:
            cleaner.return_value = True
        trip_cleaners[1].return_value = False
        stop_event_cleaners = [mock.MagicMock() for __ in range(3)]
        gtfs_cleaner = gtfsrealtimeparser.TripDataCleaner(
            trip_cleaners, stop_event_cleaners
        )

        stop_event = models.TripStopTime()
        trip = models.Trip()
        trip.stop_times.append(stop_event)

        clean_trips = gtfs_cleaner.clean([trip])

        self.assertEqual([], clean_trips)
        trip_cleaners[0].assert_called_once_with(trip)
        trip_cleaners[1].assert_called_once_with(trip)
        trip_cleaners[2].assert_not_called()
        for cleaner in stop_event_cleaners:
            cleaner.assert_not_called()
