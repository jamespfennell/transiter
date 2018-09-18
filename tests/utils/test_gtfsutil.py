import unittest
from google.transit import gtfs_realtime_pb2 as gtfs
from transiter.utils import gtfsutil

class TestGtfsUtil(unittest.TestCase):
    def test_gtfs_to_json(self):
        gtfs = _create_gtfs()
        json = gtfsutil.gtfs_to_json(gtfs)

        self.assertDictEqual(json, _create_json())

def _create_gtfs():
    root = gtfs.FeedMessage()
    header = root.header

    header.gtfs_realtime_version = "2.0"
    root.header.incrementality = 0 #=header.Incrementality.Value('FULL_DATASET')
    header.timestamp = 1000

    entity_1 = root.entity.add()
    entity_1.id = "1"

    entity_2 = root.entity.add()
    entity_2.id = "2"


    print(root)

    return root.SerializeToString()

def _create_json():
    json = {
        'header': {
            'gtfs_realtime_version': '2.0',
            'incrementality': 0,
            'timestamp': 1000
        },
        'entity': [
            {
            'id': '1'
            },
            {
            'id': '2'
            }
        ]
    }
    return json
