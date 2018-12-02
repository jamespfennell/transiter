import unittest
from unittest import mock
from transiter.services.update import tripupdater
from transiter import models


class TestTripDataCleaner(unittest.TestCase):

    def test_clean_all_good(self):
        """[Trip updater] All good"""

        trip_cleaners = [mock.MagicMock() for __ in range(3)]
        for cleaner in trip_cleaners:
            cleaner.return_value = True
        stop_event_cleaners = [mock.MagicMock() for __ in range(3)]
        gtfs_cleaner = tripupdater.TripDataCleaner(
            trip_cleaners, stop_event_cleaners)

        stop_event = models.StopTimeUpdate()
        trip = models.Trip()
        trip.stop_events.append(stop_event)

        clean_trips = gtfs_cleaner.clean([trip])

        self.assertEqual([trip], clean_trips)
        for cleaner in trip_cleaners:
            cleaner.assert_called_once_with(trip)
        for cleaner in stop_event_cleaners:
            cleaner.assert_called_once_with(stop_event)

    def test_clean_buggy_trip(self):
        """[GTFS Realtime cleaner] Buggy trip"""

        trip_cleaners = [mock.MagicMock() for __ in range(3)]
        for cleaner in trip_cleaners:
            cleaner.return_value = True
        trip_cleaners[1].return_value = False
        stop_event_cleaners = [mock.MagicMock() for __ in range(3)]
        gtfs_cleaner = tripupdater.TripDataCleaner(
            trip_cleaners, stop_event_cleaners)

        stop_event = models.StopTimeUpdate()
        trip = models.Trip()
        trip.stop_events.append(stop_event)

        clean_trips = gtfs_cleaner.clean([trip])

        self.assertEqual([], clean_trips)
        trip_cleaners[0].assert_called_once_with(trip)
        trip_cleaners[1].assert_called_once_with(trip)
        trip_cleaners[2].assert_not_called()
        for cleaner in stop_event_cleaners:
            cleaner.assert_not_called()
