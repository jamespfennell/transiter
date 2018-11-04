import copy
import datetime
import unittest
from unittest import mock
from transiter.systems.nycsubway import gtfsupdater
from transiter.database import models


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

    def test_invert_j_train_direction_in_bushwick(self):
        """[NYC Subway cleaner] Invert J train direction in Bushwick N->S"""

        stop_event = {'stop_id': 'M12N'}
        trip = {'route_id': 'J'}

        gtfsupdater._NycSubwayGtfsCleaner.invert_j_train_direction_in_bushwick(
            stop_event, trip)

        self.assertEqual(stop_event['stop_id'], 'M12S')

    def test_invert_j_train_direction_in_bushwick_two(self):
        """[NYC Subway cleaner] Invert J train direction in Bushwick S->N"""

        stop_event = {'stop_id': 'M12S'}
        trip = {'route_id': 'J'}

        gtfsupdater._NycSubwayGtfsCleaner.invert_j_train_direction_in_bushwick(
            stop_event, trip)

        self.assertEqual(stop_event['stop_id'], 'M12N')

    def test_invert_j_train_direction_in_bushwick_irrelevant_stop(self):
        """[NYC Subway cleaner] Invert J train direction in Bushwick, irrelevant stop"""

        stop_event = {'stop_id': 'M20N'}
        trip = {'route_id': 'J'}

        gtfsupdater._NycSubwayGtfsCleaner.invert_j_train_direction_in_bushwick(
            stop_event, trip)

        self.assertEqual(stop_event['stop_id'], 'M20N')

    def test_invert_j_train_direction_in_bushwick_irrelevant_route(self):
        """[NYC Subway cleaner] Invert J train direction in Bushwick, irrelevant route"""

        stop_event = {'stop_id': 'M12N'}
        trip = {'route_id': 'A'}

        gtfsupdater._NycSubwayGtfsCleaner.invert_j_train_direction_in_bushwick(
            stop_event, trip)

        self.assertEqual(stop_event['stop_id'], 'M12N')

    def test_delete_trips_with_route_id_ss(self):
        """[NYC Subway cleaner] Delete trips with route_id=SS"""

        trip = {'route_id': 'SS'}

        response = gtfsupdater._NycSubwayGtfsCleaner.delete_trips_with_route_id_ss(trip)

        self.assertFalse(response)

    def test_delete_trips_with_route_id_ss_no_delete(self):
        """[NYC Subway cleaner] Delete trips with route_id=SS - no delete case"""

        trip = {'route_id': 'SI'}

        response = gtfsupdater._NycSubwayGtfsCleaner.delete_trips_with_route_id_ss(trip)

        self.assertTrue(response)

    def test_delete_first_stop_event_slow_updating_trips__one_stop_id(self):
        """[NYC Subway cleaner] Delete slow updating trips - one stop case"""
        trip = {
            'stop_events': ['A']
        }
        trip_copy = copy.deepcopy(trip)

        gtfsupdater._NycSubwayGtfsCleaner.delete_first_stop_event_slow_updating_trips(
            trip)

        self.assertEqual(trip, trip_copy)

    def test_delete_first_stop_event_slow_updating_trips__no_update_time(self):
        """[NYC Subway cleaner] Delete slow updating trips - no update time"""
        trip = {
            'last_update_time': None,
            'stop_events': [1, 2]
        }
        trip_copy = copy.deepcopy(trip)

        gtfsupdater._NycSubwayGtfsCleaner.delete_first_stop_event_slow_updating_trips(
            trip)

        self.assertEqual(trip, trip_copy)

    DATETIME_1 = datetime.datetime(2018, 11, 5, 13, 0, 0)
    DATETIME_2 = datetime.datetime(2018, 11, 5, 13, 0, 10)
    DATETIME_3 = datetime.datetime(2018, 11, 5, 13, 0, 20)
    DATETIME_4 = datetime.datetime(2018, 11, 5, 13, 0, 30)

    def test_delete_first_stop_event_slow_updating_trips__first_stop_in_the_future(
            self):
        """[NYC Subway cleaner] Delete slow updating trips - first stop in the future"""
        trip = {
            'last_update_time': self.DATETIME_1,
            'stop_events': [
                {
                    'arrival_time': None,
                    'departure_time': self.DATETIME_4
                },
                'Second'
            ]
        }
        trip_copy = copy.deepcopy(trip)

        gtfsupdater._NycSubwayGtfsCleaner.delete_first_stop_event_slow_updating_trips(
            trip)

        self.assertEqual(trip, trip_copy)

    @mock.patch('transiter.systems.nycsubway.gtfsupdater.timestamp_to_datetime')
    def test_delete_first_stop_event_slow_updating_trips__updated_recently(
            self, timestamp_to_datetime):
        """[NYC Subway cleaner] Delete slow updating trips - first stop in the future"""
        trip = {
            'last_update_time': self.DATETIME_1,
            'stop_events': [
                {
                    'arrival_time': None,
                    'departure_time': self.DATETIME_4
                },
                'Second'
            ]
        }
        trip_copy = copy.deepcopy(trip)
        timestamp_to_datetime.return_value = self.DATETIME_2

        gtfsupdater._NycSubwayGtfsCleaner.delete_first_stop_event_slow_updating_trips(
            trip)

        self.assertEqual(trip, trip_copy)

    @mock.patch('transiter.systems.nycsubway.gtfsupdater.timestamp_to_datetime')
    def test_delete_first_stop_event_slow_updating_trips__stale(
            self, timestamp_to_datetime):
        """[NYC Subway cleaner] Delete slow updating trips - stale data"""
        trip = {
            'last_update_time': self.DATETIME_2,
            'stop_events': [
                {
                    'arrival_time': self.DATETIME_1,
                    'departure_time': self.DATETIME_1
                },
                'Second'
            ]
        }
        trip_copy = copy.deepcopy(trip)
        timestamp_to_datetime.return_value = self.DATETIME_4

        gtfsupdater._NycSubwayGtfsCleaner.delete_first_stop_event_slow_updating_trips(
            trip)

        trip_copy['stop_events'].pop(0)

        self.assertEqual(trip, trip_copy)

    def test_generate_trip_start_time(self):
        second = 30
        minute = 23
        hour = 3
        day = 13
        month = 2
        year = 2017
        start_date = '{:04d}{:02d}{:02d}'.format(year, month, day)
        trip_id = '{:06d}_IGNORED'.format(((hour*3600+minute*60+second)*10)//6)
        expected = gtfsupdater.eastern.localize(
            datetime.datetime(year, month, day, hour, minute, second)
        )

        actual = gtfsupdater.generate_trip_start_time(trip_id, start_date)

        self.assertEqual(expected, actual)

    @mock.patch('transiter.systems.nycsubway.gtfsupdater.generate_trip_start_time')
    def test_generate_trip_uid(self, generate_trip_start_time):
        trip_id = mock.MagicMock()
        start_date = mock.MagicMock()
        route_id = 'A'
        direction = 'B'
        start_timestamp = 12345
        dt = mock.MagicMock()
        dt.timestamp.return_value = start_timestamp
        generate_trip_start_time.return_value = dt

        expected = '{}{}{}'.format(route_id, direction, start_timestamp)

        actual = gtfsupdater.generate_trip_uid(
            trip_id, start_date, route_id, direction)

        self.assertEqual(expected, actual)

        generate_trip_start_time.assert_called_once_with(trip_id, start_date)
        dt.timestamp.assert_called_once_with()

    @mock.patch('transiter.systems.nycsubway.gtfsupdater.generate_trip_uid')
    @mock.patch('transiter.systems.nycsubway.gtfsupdater.generate_trip_start_time')
    def test_transform_trip_data(self, generate_trip_start_time, generate_trip_uid):
        trip_id = mock.MagicMock()
        start_date = mock.MagicMock()
        route_id = mock.MagicMock()
        new_trip_id = mock.MagicMock()
        start_time = mock.MagicMock()
        trip = {
            'direction_id': True,
            'trip_id': trip_id,
            'start_date': start_date,
            'route_id': route_id
        }
        expected_trip = {
            'direction_id': True,
            'trip_id': new_trip_id,
            'start_date': start_date,
            'start_time': start_time,
            'route_id': route_id
        }

        generate_trip_start_time.return_value = start_time
        generate_trip_uid.return_value = new_trip_id

        trip['start_time'] = start_time
        trip['trip_id'] = new_trip_id

        gtfsupdater._NycSubwayGtfsCleaner.transform_trip_data(trip)

        self.assertDictEqual(expected_trip, trip)


class TestGtfsRealtimeCleaner(unittest.TestCase):

    def test_clean_all_good(self):
        """[GTFS Realtime cleaner] All good"""
        gtfs_cleaner = gtfsupdater._NycSubwayGtfsCleaner()

        trip_cleaners = [mock.MagicMock() for __ in range(3)]
        gtfs_cleaner.trip_cleaners = trip_cleaners
        for cleaner in trip_cleaners:
            cleaner.return_value = True
        stop_event_cleaners = [mock.MagicMock() for __ in range(3)]
        gtfs_cleaner.stop_event_cleaners = stop_event_cleaners

        stop_event = mock.MagicMock()
        trip = {
            'stop_events': [
                stop_event
            ]
        }
        data = {'trips': [trip]}
        old_data = copy.deepcopy(data)

        gtfs_cleaner.clean(data)

        self.assertDictEqual(old_data, data)
        for cleaner in trip_cleaners:
            cleaner.assert_called_once_with(trip)
        for cleaner in stop_event_cleaners:
            cleaner.assert_called_once_with(stop_event, trip)

    def test_clean_buggy_trip(self):
        """[GTFS Realtime cleaner] Buggy trip"""
        gtfs_cleaner = gtfsupdater._NycSubwayGtfsCleaner()

        trip_cleaners = [mock.MagicMock() for __ in range(3)]
        gtfs_cleaner.trip_cleaners = trip_cleaners
        for cleaner in trip_cleaners:
            cleaner.return_value = True
        trip_cleaners[1].return_value = False
        stop_event_cleaners = [mock.MagicMock() for __ in range(3)]
        gtfs_cleaner.stop_event_cleaners = stop_event_cleaners

        stop_event = mock.MagicMock()
        trip = {
            'stop_events': [
                stop_event
            ]
        }
        data = {'trips': [trip]}
        expected_data = {'trips': []}

        gtfs_cleaner.clean(data)

        self.assertDictEqual(expected_data, data)
        trip_cleaners[0].assert_called_once_with(trip)
        trip_cleaners[1].assert_called_once_with(trip)
        trip_cleaners[2].assert_not_called()
        for cleaner in stop_event_cleaners:
            cleaner.assert_not_called()


