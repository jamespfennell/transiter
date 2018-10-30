import datetime
import unittest
from unittest import mock
from transiter.systems.nycsubway import gtfsupdater


class TestMergeInExtensionData(unittest.TestCase):

    TRAIN_ID = "Train ID"
    DIRECTION_ID = False
    ACTUAL_TRACK = '1'
    SCHEDULED_TRACK = '2'
    STATUS_RUNNING = 'RUNNING'
    STATUS_SCHEDULED = 'SCHEDULED'

    def test_merge_in_trip_update(self):
        """[NYC Subway extension] Merge in trip update data"""
        nyct_feed_header = mock.MagicMock()

        nyct_trip_descriptor_dict = {
            'train_id': self.TRAIN_ID,
            'direction': 'NORTH',
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
                            'direction_id': self.DIRECTION_ID,
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
        """[NYC Subway extension] Merge in vehicle data"""
        nyct_feed_header = mock.MagicMock()

        nyct_trip_descriptor_dict = {
            'train_id': self.TRAIN_ID,
            'direction': 'NORTH',
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
                            'direction_id': self.DIRECTION_ID,
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
        """[NYC Subway cleaner] Fix 5X route IDs"""
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
        """[NYC Subway cleaner] Delete trips without route Ids"""
        data = {
            'route_id': ''
        }

        response = gtfsupdater._NycSubwayGtfsCleaner.fix_route_ids(data)

        self.assertFalse(response)

    def test_delete_old_scheduled_trips_delete(self):
        """[NYC Subway cleaner] Delete old scheduled trips that haven't started"""
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
        """[NYC Subway cleaner] Don't delete scheduled trips that have started"""
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
        """[NYC Subway cleaner] Don't delete scheduled trips that aren't old"""
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

    def test_transform_stop_ids(self):
        """[NYC Subway cleaner] Tranform stop IDs in stop time updates"""
        stop_event = {
            'stop_id': 'ABCN'
        }
        expected_output = {
            'stop_id': 'ABC',
            'direction': 'N',
            'future': True
        }

        response = gtfsupdater._NycSubwayGtfsCleaner.transform_stop_ids(
            stop_event, {})

        self.assertTrue(response)
        self.assertDictEqual(stop_event, expected_output)