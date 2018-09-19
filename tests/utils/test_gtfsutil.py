import unittest
from google.transit import gtfs_realtime_pb2 as gtfs
from transiter.utils import gtfsutil

class TestGtfsUtil(unittest.TestCase):
    def test_gtfs_to_json(self):
        gtfs = _create_gtfs()
        json = gtfsutil.gtfs_to_json(gtfs)

        self.assertDictEqual(json, _create_json())

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
            'id': ENTITY_1_ID
            },
            {
            'id': ENTITY_2_ID
            }
        ]
    }
    return json
