from unittest import mock

from transiter import models
from transiter.services.update import tripupdater
from ... import testutil


class TestTripUpdater(testutil.TestCase(tripupdater)):
    SYSTEM_ID = "8"
    ROUTE_1_ID = "1"
    ROUTE_1_PK = 2
    ROUTE_2_ID = "3"
    ROUTE_2_PK = 4
    STOP_IDS = ["5", "6", "7"]
    STOP_IDS_2 = ["5", "6", "9"]
    TRIP_ID = "10"
    TRIP_PK = 11

    def setUp(self):

        self.system = models.System(id=self.SYSTEM_ID)
        self.route_1 = models.Route(id=self.ROUTE_1_ID, pk=self.ROUTE_1_PK)
        self.route_2 = models.Route(id=self.ROUTE_2_ID, pk=self.ROUTE_2_PK)
        self.system.routes = [self.route_1, self.route_2]

        self.trip_1 = models.Trip(
            pk=self.TRIP_PK, id=self.TRIP_ID, route_id=self.ROUTE_1_ID
        )
        self.trip_1.stop_times = [
            models.TripStopTime(stop_pk=int(stop_id), stop_id=stop_id, stop_sequence=i)
            for i, stop_id in enumerate(self.STOP_IDS)
        ]
        self.trip_2 = models.Trip(route_id=self.ROUTE_2_ID)
        self.trip_2.stop_times = [
            models.TripStopTime(stop_id=stop_id) for stop_id in self.STOP_IDS_2
        ]

        self.database = self.mockImportedModule(tripupdater.dbconnection)
        self.session = mock.MagicMock()
        self.database.get_session.return_value = self.session
        self.tripdam = self.mockImportedModule(tripupdater.tripdam)
        self.stopdam = self.mockImportedModule(tripupdater.stopdam)
        self.servicemapmanager = self.mockImportedModule(tripupdater.servicemapmanager)

    @testutil.patch_function(tripupdater._sync_trips_in_route)
    def test_sync_trips(self, _sync_trips_in_route):
        """[Trip updater] Sync trips coordinating method, some routes"""

        _sync_trips_in_route.return_value = True
        stop_id_to_pk = {stop_id: int(stop_id) for stop_id in self.STOP_IDS}
        self.stopdam.get_id_to_pk_map_in_system.return_value = stop_id_to_pk

        tripupdater.sync_trips(
            self.system, [self.trip_1, self.trip_2], [self.ROUTE_1_ID]
        )

        _sync_trips_in_route.assert_called_once_with(
            self.route_1, [self.trip_1], stop_id_to_pk
        )
        self.stopdam.get_id_to_pk_map_in_system.assert_called_once_with(
            self.SYSTEM_ID, set(self.STOP_IDS)
        )
        self.servicemapmanager.calculate_realtime_service_map_for_route.assert_called_once_with(
            self.route_1
        )

    @testutil.patch_function(tripupdater._sync_trips_in_route)
    def test_sync_trips_all_routes(self, _sync_trips_in_route):
        """[Trip updater] Sync trips coordinating method, all routes"""

        _sync_trips_in_route.return_value = True
        stop_id_to_pk = {stop_id: int(stop_id) for stop_id in self.STOP_IDS}
        self.stopdam.get_id_to_pk_map_in_system.return_value = stop_id_to_pk

        tripupdater.sync_trips(self.system, [self.trip_1, self.trip_2])

        print(_sync_trips_in_route.mock_calls)
        _sync_trips_in_route.assert_has_calls(
            [
                mock.call(self.route_1, [self.trip_1], stop_id_to_pk),
                mock.call(self.route_2, [self.trip_2], stop_id_to_pk),
            ],
            any_order=True,
        )
        self.stopdam.get_id_to_pk_map_in_system.assert_called_once_with(
            self.SYSTEM_ID, set(self.STOP_IDS).union(self.STOP_IDS_2)
        )
        self.servicemapmanager.calculate_realtime_service_map_for_route.assert_has_calls(
            [mock.call(self.route_1), mock.call(self.route_2)], any_order=True
        )

    def test_sync_trips_in_route__new_trip(self):
        """[Trip updater] Sync trips in routes - new trip"""
        self.tripdam.list_all_in_route_by_pk.return_value = []

        stop_id_to_stop_pk = {stop_id: int(stop_id) for stop_id in self.STOP_IDS}
        # Make the first stop invalid
        del stop_id_to_stop_pk[self.STOP_IDS[0]]

        result = tripupdater._sync_trips_in_route(
            self.route_1, [self.trip_1], stop_id_to_stop_pk
        )

        self.assertTrue(result)
        self.assertEqual(
            [int(self.STOP_IDS[1]), int(self.STOP_IDS[2])],
            [stop_time.stop_pk for stop_time in self.trip_1.stop_times],
        )

        self.tripdam.list_all_in_route_by_pk.assert_called_once_with(self.ROUTE_1_PK)

    def test_sync_trips_in_route__no_more_trips(self):
        """[Trip updater] Sync trips in routes - no more trips anymore"""

        self.tripdam.list_all_in_route_by_pk.return_value = [self.trip_1]

        result = tripupdater._sync_trips_in_route(self.route_1, [], {})

        self.assertTrue(result)

        self.tripdam.list_all_in_route_by_pk.assert_called_once_with(self.ROUTE_1_PK)

    def test_sync_trips_in_route__still_no_trips(self):
        """[Trip updater] Sync trips in routes - still no trips"""
        self.tripdam.list_all_in_route_by_pk.return_value = []

        result = tripupdater._sync_trips_in_route(self.route_1, [], {})

        self.assertFalse(result)

        self.tripdam.list_all_in_route_by_pk.assert_called_once_with(self.ROUTE_1_PK)

    def test_sync_trips_in_route__updated_trip_same_map(self):
        """[Trip updater] Sync trips in routes - updated trip, same map"""

        self.tripdam.list_all_in_route_by_pk.return_value = [self.trip_1]

        stop_id_to_stop_pk = {stop_id: int(stop_id) for stop_id in self.STOP_IDS}
        feed_trip = models.Trip(id=self.TRIP_ID)
        feed_trip.stop_times = [
            models.TripStopTime(stop_id=self.STOP_IDS[1], stop_sequence=1),
            models.TripStopTime(stop_id=self.STOP_IDS[2], stop_sequence=2),
        ]

        result = tripupdater._sync_trips_in_route(
            self.route_1, [feed_trip], stop_id_to_stop_pk
        )

        self.assertFalse(result)
        self.assertEqual(
            [int(self.STOP_IDS[0]), int(self.STOP_IDS[1]), int(self.STOP_IDS[2])],
            [stop_time.stop_pk for stop_time in feed_trip.stop_times],
        )
        self.assertFalse(feed_trip.stop_times[0].future)

        self.tripdam.list_all_in_route_by_pk.assert_called_once_with(self.ROUTE_1_PK)

    def test_sync_trips_in_route__updated_trip_new_map(self):
        """[Trip updater] Sync trips in routes - update tripm new map"""

        self.tripdam.list_all_in_route_by_pk.return_value = [self.trip_1]

        stop_id_to_stop_pk = {
            stop_id: int(stop_id)
            for stop_id in set(self.STOP_IDS).union(self.STOP_IDS_2)
        }
        feed_trip = models.Trip(id=self.TRIP_ID)
        feed_trip.stop_times = [
            models.TripStopTime(stop_id=self.STOP_IDS[1], stop_sequence=1),
            models.TripStopTime(stop_id=self.STOP_IDS_2[2], stop_sequence=2),
        ]

        result = tripupdater._sync_trips_in_route(
            self.route_1, [feed_trip], stop_id_to_stop_pk
        )

        self.assertTrue(result)
        self.assertEqual(
            [int(self.STOP_IDS[0]), int(self.STOP_IDS[1]), int(self.STOP_IDS_2[2])],
            [stop_time.stop_pk for stop_time in feed_trip.stop_times],
        )
        self.assertFalse(feed_trip.stop_times[0].future)

        self.tripdam.list_all_in_route_by_pk.assert_called_once_with(self.ROUTE_1_PK)

    def test_clean_all_good(self):
        """[Trip updater] Trip cleaner - All good"""

        trip_cleaners = [mock.MagicMock() for __ in range(3)]
        for cleaner in trip_cleaners:
            cleaner.return_value = True
        stop_event_cleaners = [mock.MagicMock() for __ in range(3)]
        gtfs_cleaner = tripupdater.TripDataCleaner(trip_cleaners, stop_event_cleaners)

        stop_event = models.TripStopTime()
        trip = models.Trip()
        trip.stop_times.append(stop_event)

        clean_trips = gtfs_cleaner.clean("", [trip])

        self.assertEqual([trip], clean_trips)
        for cleaner in trip_cleaners:
            cleaner.assert_called_once_with("", trip)
        for cleaner in stop_event_cleaners:
            cleaner.assert_called_once_with("", stop_event)

    def test_clean_buggy_trip(self):
        """[Trip updater] Trip cleaner - Buggy trip"""

        trip_cleaners = [mock.MagicMock() for __ in range(3)]
        for cleaner in trip_cleaners:
            cleaner.return_value = True
        trip_cleaners[1].return_value = False
        stop_event_cleaners = [mock.MagicMock() for __ in range(3)]
        gtfs_cleaner = tripupdater.TripDataCleaner(trip_cleaners, stop_event_cleaners)

        stop_event = models.TripStopTime()
        trip = models.Trip()
        trip.stop_times.append(stop_event)

        clean_trips = gtfs_cleaner.clean("", [trip])

        self.assertEqual([], clean_trips)
        trip_cleaners[0].assert_called_once_with("", trip)
        trip_cleaners[1].assert_called_once_with("", trip)
        trip_cleaners[2].assert_not_called()
        for cleaner in stop_event_cleaners:
            cleaner.assert_not_called()
