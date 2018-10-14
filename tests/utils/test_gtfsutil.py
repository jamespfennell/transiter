import unittest
from unittest import mock
from google.transit import gtfs_realtime_pb2 as gtfs
from transiter.utils import gtfsutil


class TestGtfsRealtimeExtension(unittest.TestCase):

    PB_MODULE = 'Module One'
    BASE_MODULE = 'Module Two'

    @mock.patch('transiter.utils.gtfsutil.importlib')
    def test_gtfs_realtime_extension(self, importlib):
        """[Read GTFS Realtime] Feed extension activation"""
        gtfs_realtime_extension = gtfsutil.GtfsRealtimeExtension(
            self.PB_MODULE, self.BASE_MODULE)

        gtfs_realtime_extension.activate()

        importlib.import_module.assert_called_once_with(
            self.PB_MODULE, self.BASE_MODULE)


class TestReadGtfsRealtime(unittest.TestCase):

    RAW_CONTENT = 'Some content'
    PARSED_CONTENT = 'Transformed'

    def setUp(self):
        self.gtfs_feed = mock.MagicMock()

        self. patch1 = mock.patch('transiter.utils.gtfsutil.gtfs_realtime_pb2')
        self.gtfs_realtime_pb2 = self.patch1.start()
        self.gtfs_realtime_pb2.FeedMessage.return_value = self.gtfs_feed

        self.patch2 = mock.patch('transiter.utils.gtfsutil._read_protobuf_message')
        self._read_protobuf_message = self.patch2.start()
        self._read_protobuf_message.return_value = self.PARSED_CONTENT

    def tearDown(self):
        self.gtfs_realtime_pb2.FeedMessage.assert_called_once_with()
        self.gtfs_feed.ParseFromString.assert_called_once_with(self.RAW_CONTENT)
        self.patch1.stop()

        self._read_protobuf_message.assert_called_once_with(self.gtfs_feed)
        self.patch2.stop()

    def test_read_gtfs_realtime(self):
        """[Read GTFS Realtime] Read basic feed subtask scheduling"""
        actual_response = gtfsutil.read_gtfs_realtime(self.RAW_CONTENT)

        self.assertEqual(actual_response, self.PARSED_CONTENT)

    def test_read_gtfs_realtime_with_extension(self):
        """[Read GTFS Realtime] Read feed with extension subtask scheduling"""
        extension = mock.MagicMock()

        actual_response = gtfsutil.read_gtfs_realtime(self.RAW_CONTENT, extension)

        self.assertEqual(actual_response, self.PARSED_CONTENT)

        extension.activate.assert_called_once_with()


class TestReadProtobufMessage(unittest.TestCase):

    GTFS_REALTIME_VERSION = '2.0'
    INCREMENTALITY = "FULL_DATASET"
    INCREMENTALITY_INT = gtfs.FeedHeader.Incrementality.Value(INCREMENTALITY)
    TIMESTAMP = 4
    ENTITY_1_ID = '1'
    ENTITY_2_ID = '2'
    CONGESTION_ONE = 'STOP_AND_GO'
    CONGESTION_ONE_INT = gtfs.VehiclePosition.CongestionLevel.Value(CONGESTION_ONE)
    CONGESTION_TWO = 'CONGESTION'
    CONGESTION_TWO_INT = gtfs.VehiclePosition.CongestionLevel.Value(CONGESTION_TWO)

    def test_read_protobuf_message(self):
        """[Read GTFS Realtime] Read protobuf message"""
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
            'header': {
                'gtfs_realtime_version': self.GTFS_REALTIME_VERSION,
                'incrementality': self.INCREMENTALITY,
                'timestamp': self.TIMESTAMP
            },
            'entity': [
                {
                    'id': self.ENTITY_1_ID,
                    'vehicle': {
                        'congestion_level': self.CONGESTION_ONE
                    }
                },
                {
                    'id': self.ENTITY_2_ID,
                    'vehicle': {
                        'congestion_level': self.CONGESTION_TWO
                    }
                }
            ]
        }

        actual_data = gtfsutil._read_protobuf_message(root)

        self.assertDictEqual(actual_data, expected_data)


class TestTransformGtfsRealtime(unittest.TestCase):

    GTFS_REALTIME_VERSION = '2.0'
    INCREMENTALITY = 'FULL_DATASET'
    INCREMENTALITY_INT = gtfs.FeedHeader.Incrementality.Value(INCREMENTALITY)
    FEED_UPDATE_TIMESTAMP = 4
    TRIP_UPDATE_TIMESTAMP = 5
    STOP_ONE_ID = "Stop 1"
    STOP_ONE_ARR_TIMESTAMP = 6
    STOP_ONE_DEP_TIMESTAMP = 7
    STOP_TWO_ID = "Stop 2"
    STOP_TWO_ARR_TIMESTAMP = 8
    ENTITY_1_ID = '1'
    ENTITY_2_ID = '2'
    TRIP_ID = "Trip 1"
    ROUTE_ID = 'L'
    START_DATE = '26031990'
    TRAIN_ID = 'Train ID'
    TRIP_DIRECTION = 'North'
    CURRENT_STATUS = 'Stopped'
    CURRENT_STOP_SEQUENCE = 14

    def setUp(self):
        self.timestamp_to_datetime \
            = gtfsutil._GtfsRealtimeToTransiterTransformer._timestamp_to_datetime

    def test_transform_feed_metadata(self):
        """[GTFS Realtime transformer] Transform feed metadata"""
        raw_data = {
            'header': {
                'timestamp': self.FEED_UPDATE_TIMESTAMP,
                'other_field': 'other value'
            },
            'other_field': 'other value'
        }
        expected_transformed_metadata = {
            'timestamp': self.timestamp_to_datetime(self.FEED_UPDATE_TIMESTAMP)
        }
        transformer = gtfsutil._GtfsRealtimeToTransiterTransformer(raw_data)

        transformer._transform_feed_metadata()

        self.assertDictEqual(
            expected_transformed_metadata, transformer._transformed_metadata)

    def test_group_trip_entities(self):
        """[GTFS Realtime transformer] Group trip entities"""
        trip_dict = {'trip_id': self.TRIP_ID}
        trip = mock.MagicMock()
        trip.__getitem__.side_effect = trip_dict.__getitem__

        entity_dict = {'trip': trip}
        trip_update = mock.MagicMock()
        trip_update.__getitem__.side_effect = entity_dict.__getitem__
        vehicle = mock.MagicMock()
        vehicle.__getitem__.side_effect = entity_dict.__getitem__

        raw_data = {
            'entity': [
                {
                    'trip_update': trip_update
                },
                {
                    'vehicle': vehicle
                },
                {
                    'unknown': 'unknown'
                }
            ]
        }
        expected_raw_entities = {
            self.TRIP_ID: {
                'trip': trip,
                'trip_update': trip_update,
                'vehicle': vehicle
            }
        }

        transformer = gtfsutil._GtfsRealtimeToTransiterTransformer(raw_data)
        transformer._group_trip_entities()

        self.assertDictEqual(expected_raw_entities,
                             transformer._trip_id_to_raw_entities)

    def test_transform_trip_base_data(self):
        """[GTFS Realtime transformer] Transform trip base data"""
        transformer = gtfsutil._GtfsRealtimeToTransiterTransformer(None)
        transformer._trip_id_to_raw_entities = {
            self.TRIP_ID: {
                'trip': {
                    'trip_id': self.TRIP_ID,
                    'route_id': self.ROUTE_ID,
                    'start_date': self.START_DATE,
                    'train_id': self.TRAIN_ID,
                    'direction': self.TRIP_DIRECTION,
                }
            }
        }
        transformer._feed_time = self.FEED_UPDATE_TIMESTAMP

        expected_transformed_base_data = {
            self.TRIP_ID: {
                'trip_id': self.TRIP_ID,
                'route_id': self.ROUTE_ID,
                'start_date': self.START_DATE,
                'train_id': self.TRAIN_ID,
                'direction': self.TRIP_DIRECTION,
                'current_status': None,
                'current_stop_sequence': 0,
                'last_update_time': None,
                'feed_update_time': self.FEED_UPDATE_TIMESTAMP
            }
        }

        transformer._transform_trip_base_data()

        self.assertDictEqual(
            expected_transformed_base_data,
            transformer._trip_id_to_transformed_entity)
        self.assertSetEqual(transformer._feed_route_ids, set(self.ROUTE_ID))

    def test_transform_trip_base_data_with_vehicle(self):
        """[GTFS Realtime transformer] Transform trip base data with vehicle"""
        transformer = gtfsutil._GtfsRealtimeToTransiterTransformer(None)
        transformer._trip_id_to_raw_entities = {
            self.TRIP_ID: {
                'trip': {
                    'trip_id': self.TRIP_ID,
                    'route_id': self.ROUTE_ID,
                    'start_date': self.START_DATE,
                    'train_id': self.TRAIN_ID,
                    'direction': self.TRIP_DIRECTION,
                },
                'vehicle': {
                    'timestamp': self.TRIP_UPDATE_TIMESTAMP,
                    'current_status': self.CURRENT_STATUS,
                    'current_stop_sequence': self.CURRENT_STOP_SEQUENCE,
                }
            }
        }
        transformer._feed_time = self.FEED_UPDATE_TIMESTAMP

        expected_transformed_base_data = {
            self.TRIP_ID: {
                'trip_id': self.TRIP_ID,
                'route_id': self.ROUTE_ID,
                'start_date': self.START_DATE,
                'train_id': self.TRAIN_ID,
                'direction': self.TRIP_DIRECTION,
                'last_update_time': self.timestamp_to_datetime(
                    self.TRIP_UPDATE_TIMESTAMP),
                'current_status': self.CURRENT_STATUS,
                'current_stop_sequence': self.CURRENT_STOP_SEQUENCE,
                'feed_update_time': self.FEED_UPDATE_TIMESTAMP
            }
        }

        transformer._transform_trip_base_data()

        self.assertDictEqual(
            expected_transformed_base_data,
            transformer._trip_id_to_transformed_entity)
        self.assertSetEqual(transformer._feed_route_ids, set(self.ROUTE_ID))

    def test_transform_trip_stop_events_short_circuit(self):
        """[GTFS Realtime transformer] Transform trip base data with no stops"""
        transformer = gtfsutil._GtfsRealtimeToTransiterTransformer(None)
        transformer._trip_id_to_raw_entities = {
            self.TRIP_ID: {
                'trip': 'Data'
            }
        }
        expected_transformed_entity = {
            self.TRIP_ID: {
                'stop_events': []
            }
        }

        transformer._transform_trip_stop_events()

        self.assertDictEqual(
            expected_transformed_entity, transformer._trip_id_to_transformed_entity)

    def test_transform_trip_stop_events(self):
        """[GTFS Realtime transformer] Transform trip stop events"""
        transformer = gtfsutil._GtfsRealtimeToTransiterTransformer(None)
        transformer._trip_id_to_raw_entities = {
            self.TRIP_ID: {
                'trip': 'Data',
                'trip_update': {
                    "stop_time_update": [
                        {
                            "arrival": {
                                "time": self.STOP_ONE_ARR_TIMESTAMP,
                            },
                            "departure": {
                                "time": self.STOP_ONE_DEP_TIMESTAMP,
                            },
                            "stop_id": self.STOP_ONE_ID,
                        },
                        {
                            "arrival": {
                                "time": self.STOP_TWO_ARR_TIMESTAMP,
                            },
                            "stop_id": self.STOP_TWO_ID,
                        }
                    ]
                }
            }
        }
        expected_transformed_entity = {
            self.TRIP_ID: {
                'stop_events': [
                    {
                        "stop_id": self.STOP_ONE_ID,
                        "arrival_time": self.timestamp_to_datetime(
                            self.STOP_ONE_ARR_TIMESTAMP),
                        "departure_time": self.timestamp_to_datetime(
                            self.STOP_ONE_DEP_TIMESTAMP),
                        'track': None
                    },
                    {
                        "stop_id": self.STOP_TWO_ID,
                        "arrival_time": self.timestamp_to_datetime(
                            self.STOP_TWO_ARR_TIMESTAMP),
                        "departure_time": None,
                        'track': None
                    }
                ]
            }
        }

        transformer._transform_trip_stop_events()

        self.maxDiff = None
        self.assertDictEqual(
            expected_transformed_entity, transformer._trip_id_to_transformed_entity)

    def test_update_stop_event_indices(self):
        """[GTFS Realtime transformer] Update stop event indices"""
        transformer = gtfsutil._GtfsRealtimeToTransiterTransformer(None)
        transformer._trip_id_to_transformed_entity = {
            self.TRIP_ID: {
                'current_stop_sequence': 5,
                'stop_events': [
                    {},
                    {}
                ]
            }
        }

        expected_updated_entity = {
            self.TRIP_ID: {
                'current_stop_sequence': 5,
                'stop_events': [
                    {
                        'sequence_index': 6,
                    },
                    {
                        'sequence_index': 7,
                    }
                ]
            }
        }

        transformer._update_stop_event_indices()

        self.assertDictEqual(
            expected_updated_entity, transformer._trip_id_to_transformed_entity)

    def test_collect_transformed_data(self):
        """[GTFS Realtime transformer] Collect transformed data"""
        trip = mock.MagicMock()
        feed_time = mock.MagicMock()
        transformer = gtfsutil._GtfsRealtimeToTransiterTransformer(None)
        transformer._trip_id_to_transformed_entity = {
            self.TRIP_ID: trip
        }
        transformer._transformed_metadata = {
            'timestamp': feed_time
        }
        transformer._feed_route_ids = set(self.ROUTE_ID)

        expected_data = {
            'timestamp': feed_time,
            'trips': [trip],
            'route_ids': [self.ROUTE_ID]
        }

        actual_data = transformer._collect_transformed_data()

        self.assertDictEqual(expected_data, actual_data)

    def test_transform(self):
        """[GTFS Realtime transformer] Transform process subtask scheduling"""
        expected_data = mock.MagicMock()
        transformer = gtfsutil._GtfsRealtimeToTransiterTransformer(None)
        transformer._transform_feed_metadata = mock.MagicMock()
        transformer._group_trip_entities = mock.MagicMock()
        transformer._transform_trip_base_data = mock.MagicMock()
        transformer._transform_trip_stop_events = mock.MagicMock()
        transformer._update_stop_event_indices = mock.MagicMock()
        transformer._collect_transformed_data = mock.MagicMock()
        transformer._collect_transformed_data.return_value = expected_data

        actual_data = transformer.transform()

        self.assertEqual(expected_data, actual_data)

        transformer._transform_feed_metadata.assert_called_once_with()
        transformer._group_trip_entities.assert_called_once_with()
        transformer._transform_trip_base_data.assert_called_once_with()
        transformer._transform_trip_stop_events.assert_called_once_with()
        transformer._update_stop_event_indices.assert_called_once_with()
        transformer._collect_transformed_data.assert_called_once_with()
        transformer._collect_transformed_data.assert_called_once_with()

    def test_start_to_finish_parse(self):
        """[GTFS Realtime transformer] Full transformation test"""
        input = {
            'header': {
                'gtfs_realtime_version': self.GTFS_REALTIME_VERSION,
                'incrementality': self.INCREMENTALITY,
                'timestamp': self.FEED_UPDATE_TIMESTAMP
            },
            'entity': [
                {
                'id': self.ENTITY_1_ID,
                "vehicle": {
                    "trip": {
                        "trip_id": "trip_id",
                        "start_date": "20180915",
                        "route_id": "4",
                    },
                    "current_stop_sequence": 16,
                    "current_status": 2,
                    "timestamp": self.TRIP_UPDATE_TIMESTAMP,
                    "stop_id": "626S"
                    }
                },
                {
                'id': self.ENTITY_2_ID,
                "trip_update": {
                    "trip": {
                        "trip_id": "trip_id",
                        "start_date": "20180915",
                        "route_id": "4"
                    },
                    "stop_time_update": [
                        {
                            "arrival": {
                                "time": self.STOP_ONE_ARR_TIMESTAMP,
                            },
                            "departure": {
                                "time": self.STOP_ONE_DEP_TIMESTAMP,
                            },
                            "stop_id": self.STOP_ONE_ID,
                        },
                        {
                            "arrival": {
                                "time": self.STOP_TWO_ARR_TIMESTAMP,
                            },
                            "stop_id": self.STOP_TWO_ID,
                        }
                    ]
                    }
                }
            ]
        }

        timestamp_to_datetime \
            = gtfsutil._GtfsRealtimeToTransiterTransformer._timestamp_to_datetime
        expected_output = {
            "timestamp": timestamp_to_datetime(self.FEED_UPDATE_TIMESTAMP),
            "route_ids": [
                "4"
            ],
            "trips": [
                {
                    "trip_id": "trip_id",
                    'train_id': None,
                    "route_id": "4",
                    "start_date": "20180915",
                    "current_stop_sequence": 16,
                    "current_status": 2,
                    'direction': None,
                    'feed_update_time': self.timestamp_to_datetime(
                        self.FEED_UPDATE_TIMESTAMP),
                    'last_update_time': self.timestamp_to_datetime(
                        self.TRIP_UPDATE_TIMESTAMP),
                    "stop_events": [
                        {
                            "stop_id": self.STOP_ONE_ID,
                            "sequence_index": 17,
                            "arrival_time": self.timestamp_to_datetime(
                                self.STOP_ONE_ARR_TIMESTAMP),
                            "departure_time": self.timestamp_to_datetime(
                                self.STOP_ONE_DEP_TIMESTAMP),
                            'track': None
                        },
                        {
                            "stop_id": self.STOP_TWO_ID,
                            "sequence_index": 18,
                            "arrival_time": self.timestamp_to_datetime(
                                self.STOP_TWO_ARR_TIMESTAMP),
                            "departure_time": None,
                            'track': None
                        }
                    ]
                }
            ]
        }

        actual_output = gtfsutil.transform_to_transiter_structure(input)

        self.maxDiff = None
        self.assertDictEqual(actual_output, expected_output)

