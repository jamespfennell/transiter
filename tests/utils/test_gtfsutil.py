import unittest
from google.transit import gtfs_realtime_pb2 as gtfs
from transiter.utils import gtfsutil


class TestGtfsUtil(unittest.TestCase):
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


GTFS_REALTIME_VERSION = '2.0'
INCREMENTALITY = gtfs.FeedHeader.Incrementality.Value('FULL_DATASET')
TIMESTAMP = 100000

ENTITY_1_ID = '1'
ENTITY_2_ID = '2'


def _create_gtfs():
    root = gtfs.FeedMessage()
    header = root.header

    header.gtfs_realtime_version = GTFS_REALTIME_VERSION
    root.header.incrementality = INCREMENTALITY
    header.timestamp = TIMESTAMP

    entity_1 = root.entity.add()
    entity_1.id = ENTITY_1_ID

    entity_2 = root.entity.add()
    entity_2.id = ENTITY_2_ID


    print(root)

    return root.SerializeToString()

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

