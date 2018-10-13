import datetime
import unittest
from unittest import mock
from transiter.systems.nycsubway import gtfsupdater


class TestMergeInExtensionData(unittest.TestCase):

    TRAIN_ID = "Train ID"
    DIRECTION = 'Direction'
    ACTUAL_TRACK = '1'
    SCHEDULED_TRACK = '2'
    STATUS_RUNNING = 'RUNNING'
    STATUS_SCHEDULED = 'SCHEDULED'

    def test_merge_in_trip_update(self):
        nyct_feed_header = mock.MagicMock()

        nyct_trip_descriptor_dict = {
            'train_id': self.TRAIN_ID,
            'direction': self.DIRECTION,
            'is_assigned': True
        }
        nyct_trip_descriptor = mock.MagicMock()
        nyct_trip_descriptor.get.side_effect = lambda x, y: nyct_trip_descriptor_dict[x]

        nyct_stop_time_update_dict = {
            'actual_track': self.ACTUAL_TRACK,
            'scheduled_track': self.SCHEDULED_TRACK
        }
        nyct_stop_time_update = mock.MagicMock()
        nyct_stop_time_update.get.side_effect = lambda x, y: nyct_stop_time_update_dict[x]

        input_data = {
            'header': {
                'nyct_feed_header': nyct_feed_header
            },
            'entity': [
                {
                    'trip_update': {
                        'trip': {
                            'nyct_trip_descriptor': nyct_trip_descriptor
                        },
                        'stop_time_update': [
                            {
                                'nyct_stop_time_update': nyct_stop_time_update
                            }
                        ]
                    }
                }
            ]
        }

        expected_output_data = {
            'header': {},
            'entity': [
                {
                    'trip_update': {
                        'trip': {
                            'train_id': self.TRAIN_ID,
                            'direction': self.DIRECTION,
                            'status': self.STATUS_RUNNING
                        },
                        'stop_time_update': [
                            {
                                'track': self.ACTUAL_TRACK
                            }
                        ]
                    }
                }
            ]
        }

        actual_output_data = gtfsupdater.merge_in_nyc_subway_extension_data(
            input_data)

        self.maxDiff = None
        self.assertDictEqual(expected_output_data, actual_output_data)

    def test_merge_in_vehicle(self):
        nyct_feed_header = mock.MagicMock()

        nyct_trip_descriptor_dict = {
            'train_id': self.TRAIN_ID,
            'direction': self.DIRECTION,
            'is_assigned': False
        }
        nyct_trip_descriptor = mock.MagicMock()
        nyct_trip_descriptor.get.side_effect = lambda x, y: nyct_trip_descriptor_dict[x]

        nyct_stop_time_update_dict = {
            'actual_track': None,
            'scheduled_track': self.SCHEDULED_TRACK
        }
        nyct_stop_time_update = mock.MagicMock()
        nyct_stop_time_update.get.side_effect = lambda x, y: nyct_stop_time_update_dict[x]

        input_data = {
            'header': {
                'nyct_feed_header': nyct_feed_header
            },
            'entity': [
                {
                    'vehicle': {
                        'trip': {
                            'nyct_trip_descriptor': nyct_trip_descriptor
                        },
                    }
                }
            ]
        }

        expected_output_data = {
            'header': {},
            'entity': [
                {
                    'vehicle': {
                        'trip': {
                            'train_id': self.TRAIN_ID,
                            'direction': self.DIRECTION,
                            'status': self.STATUS_SCHEDULED
                        },
                    }
                }
            ]
        }

        actual_output_data = gtfsupdater.merge_in_nyc_subway_extension_data(
            input_data)

        self.maxDiff = None
        self.assertDictEqual(expected_output_data, actual_output_data)


class TestNycSubwayGtfsCleaner(unittest.TestCase):

    def test_fix_route_ids_5x(self):
        data = {
            'route_id': '5X'
        }
        expected_output_data = {
            'route_id': '5'
        }

        response = gtfsupdater._NycSubwayGtfsCleaner.fix_route_ids(data)

        self.assertTrue(response)
        self.assertDictEqual(expected_output_data, data)

    def test_fix_route_ids_no_route_id(self):
        data = {
            'route_id': ''
        }

        response = gtfsupdater._NycSubwayGtfsCleaner.fix_route_ids(data)

        self.assertFalse(response)

    def test_delete_old_scheduled_trips_delete(self):
        cleaner = gtfsupdater._NycSubwayGtfsCleaner()
        cleaner.data = {
            'timestamp': datetime.datetime.fromtimestamp(1000)
        }
        trip_data = {
            'start_time': datetime.datetime.fromtimestamp(100),
            'current_status': 'SCHEDULED'
        }

        response = cleaner.delete_old_scheduled_trips(trip_data)

        self.assertFalse(response)

    def test_delete_old_scheduled_trips_started(self):
        cleaner = gtfsupdater._NycSubwayGtfsCleaner()
        cleaner.data = {
            'timestamp': datetime.datetime.fromtimestamp(1000)
        }
        trip_data = {
            'start_time': datetime.datetime.fromtimestamp(100),
            'current_status': 'RUNNING'
        }

        response = cleaner.delete_old_scheduled_trips(trip_data)

        self.assertTrue(response)

    def test_delete_old_scheduled_trips_not_old(self):
        cleaner = gtfsupdater._NycSubwayGtfsCleaner()
        cleaner.data = {
            'timestamp': datetime.datetime.fromtimestamp(1000)
        }
        trip_data = {
            'start_time': datetime.datetime.fromtimestamp(1000),
            'current_status': 'SCHEDULED'
        }

        response = cleaner.delete_old_scheduled_trips(trip_data)

        self.assertTrue(response)
