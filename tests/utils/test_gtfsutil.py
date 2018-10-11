import unittest
from unittest import mock
from google.transit import gtfs_realtime_pb2 as gtfs
from transiter.utils import gtfsutil


class TestGtfsRealtimeExtension(unittest.TestCase):

    PB_MODULE = 'Module One'
    BASE_MODULE = 'Module Two'

    @mock.patch('transiter.utils.gtfsutil.importlib')
    def test_gtfs_realtime_extension(self, importlib):
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
        actual_response = gtfsutil.read_gtfs_realtime(self.RAW_CONTENT)

        self.assertEqual(actual_response, self.PARSED_CONTENT)

    def test_read_gtfs_realtime_with_extension(self):
        extension = mock.MagicMock()

        actual_response = gtfsutil.read_gtfs_realtime(self.RAW_CONTENT, extension)

        self.assertEqual(actual_response, self.PARSED_CONTENT)

        extension.activate.assert_called_once_with()





    """
    #def test_gtfs_to_json(self):
    #    gtfs = _create_gtfs()
    #    json = gtfsutil.gtfs_to_json(gtfs)
    #
    #    self.assertDictEqual(json, _create_json())

    def test_restructure(self):
        json_1 = gtfsutil.restructure(_create_json())
        json_2 = _create_formatted_json()
        self.maxDiff = None
        self.assertDictEqual(json_1, json_2)
    
    """

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


def _create_json():
    json = {
        'header': {
            'gtfs_realtime_version': GTFS_REALTIME_VERSION,
            'incrementality': INCREMENTALITY,
            'timestamp': TIMESTAMP
        },
        'entity': [
            {
            'id': ENTITY_1_ID,
            "vehicle": {
                "trip": {
                    "trip_id": "trip_id",
                    "start_date": "20180915",
                    "route_id": "4",
                },
                "current_stop_sequence": 16,
                "current_status": 2,
                "timestamp": 1537031806,
                "stop_id": "626S"
                }
            },
            {
            'id': ENTITY_2_ID,
            "trip_update": {
                "trip": {
                    "trip_id": "trip_id",
                    "start_date": "20180915",
                    "route_id": "4"
                },
                "stop_time_update": [
                    {
                        "arrival": {
                            "time": 1537031850
                        },
                        "departure": {
                            "time": 1537031850
                        },
                        "stop_id": "418N"
                    }
                ]
                }
            }
        ]
    }

    return json


def _create_formatted_json():
    json = {
        "timestamp": gtfsutil._timestamp_to_datetime(TIMESTAMP),
        "route_ids": [
            "4"
        ],
        "trips": [
            {
                "trip_id": "trip_id",
                "route_id": "4",
                "start_date": "20180915",
                "current_stop_sequence": 16,
                "current_status": 2,
                'feed_update_time': gtfsutil._timestamp_to_datetime(TIMESTAMP),
                'last_update_time': gtfsutil._timestamp_to_datetime(1537031806),
                "stop_events": [{
                    "stop_id": "418N",
                    "sequence_index": 17,
                    "arrival_time": gtfsutil._timestamp_to_datetime(1537031850),
                    "departure_time": gtfsutil._timestamp_to_datetime(1537031850),
                    'track': None
                }]
            }
        ]
    }
    return json

