from unittest import mock

from transiter import models
from transiter.services.update import sync
from ... import testutil


class TestSync(testutil.TestCase(sync)):
    ROUTE_1_ID = "1"
    ROUTE_2_ID = "2"
    STOP_1_ID = "3"

    def setUp(self):
        self.feed_update = models.FeedUpdate(models.Feed())

        # Attaching the class methods to a master mock allows us to verify the call
        # order: https://stackoverflow.com/questions/22677280/checking-call-order-across-multiple-mocks/22677452#22677452
        self._master_mock = mock.Mock()
        for method in [
            "_sync_routes",
            "_sync_stops",
            "_sync_scheduled_services",
            "_sync_direction_rules",
            "_sync_trips",
            "_sync_alerts",
        ]:
            self._master_mock.attach_mock(self.mockModuleAttribute(method), method)
        self._master_mock.attach_mock(
            self.mockModuleAttribute("_delete_stale_entities"), "_delete_stale_entities"
        )

    def test_all_updatable_entities_can_be_synced(self):
        """
        [Sync] Can sync all types up updatable entity
        """
        for UpdatableEntityClass in models.list_updatable_entities():
            sync.sync(self.feed_update, [UpdatableEntityClass()])

    def test_invalid_entity(self):
        """
        [Sync] Invalid entity to sync
        """
        self.assertRaises(
            TypeError, lambda: sync.sync(self.feed_update, [models.System()])
        )

    def test_no_entities(self):
        """
        [Sync] No entities provided
        """
        sync.sync(self.feed_update, [])

        self._verify_entities_synced([], [], [], [], [], [])

    def test_some_entities(self):
        """
        [Sync] Some entities
        """
        route_1_entity = models.Route(id=self.ROUTE_1_ID)
        route_2_entity = models.Route(id=self.ROUTE_2_ID)
        stop_entity = models.Stop(id=self.STOP_1_ID)

        sync.sync(self.feed_update, [route_1_entity, stop_entity, route_2_entity])

        self._verify_entities_synced(
            [route_1_entity, route_2_entity], [stop_entity], [], [], [], []
        )

    def _verify_entities_synced(
        self,
        expected_routes,
        expected_stops,
        expected_scheduled_services,
        expected_direction_rules,
        expected_trips,
        expected_alerts,
    ):
        self._master_mock.assert_has_calls(
            [
                mock.call._sync_routes(self.feed_update, expected_routes),
                mock.call._delete_stale_entities(models.Route, self.feed_update),
                mock.call._sync_stops(self.feed_update, expected_stops),
                mock.call._delete_stale_entities(models.Stop, self.feed_update),
                mock.call._sync_scheduled_services(
                    self.feed_update, expected_scheduled_services
                ),
                mock.call._delete_stale_entities(
                    models.ScheduledService, self.feed_update
                ),
                mock.call._sync_direction_rules(
                    self.feed_update, expected_direction_rules
                ),
                mock.call._delete_stale_entities(
                    models.DirectionRule, self.feed_update
                ),
                mock.call._sync_trips(self.feed_update, expected_trips),
                mock.call._delete_stale_entities(models.Trip, self.feed_update),
                mock.call._sync_alerts(self.feed_update, expected_alerts),
                mock.call._delete_stale_entities(models.Alert, self.feed_update),
            ]
        )


class TestSyncDirectionRules(testutil.TestCase(sync)):

    STOP_ID = "1"
    STOP_PK = 2
    SYSTEM_ID = "3"
    STOP_ID_2 = "4"

    def setUp(self):
        self.stopdam = self.mockImportedModule(sync.stopdam)
        self.stopdam.get_id_to_pk_map_in_system.return_value = {
            self.STOP_ID: self.STOP_PK
        }
        self.feed_update = models.FeedUpdate(models.Feed())
        self.feed_update.feed.system = models.System(id=self.SYSTEM_ID)

    @mock.patch.object(sync, "_merge_entities")
    def test_base_case(self, _merge_entities):
        """[Sync] Test sync direction rules"""
        direction_rule = models.DirectionRule(stop_id=self.STOP_ID)

        sync._sync_direction_rules(self.feed_update, [direction_rule])

        entity_to_merge = _merge_entities.call_args_list[0][0][2][0]
        self.assertEqual(self.STOP_PK, entity_to_merge.stop_pk)

    @mock.patch.object(sync, "_merge_entities")
    def test_bad_stop_id(self, _merge_entities):
        """[Sync] Test sync direction rules - bad stop ID"""
        direction_rule = models.DirectionRule(stop_id=self.STOP_ID_2)

        sync._sync_direction_rules(self.feed_update, [direction_rule])

        entities_to_merge = _merge_entities.call_args_list[0][0][2]
        self.assertEqual([], entities_to_merge)

    @mock.patch.object(sync, "_merge_entities")
    def test_no_direction_rules(self, _merge_entities):
        """[Sync] Test sync direction rules - no entities"""
        sync._sync_direction_rules(self.feed_update, [])

        _merge_entities.assert_not_called()


class TestSyncAlerts(testutil.TestCase(sync)):

    ID_1 = "1"
    ID_2 = "2"
    SYSTEM_ID = "3"
    SYSTEM_PK = 7
    ROUTE_ID_1 = "4"
    ROUTE_ID_2 = "5"
    AGENCY_ID = "6"

    @mock.patch.object(sync, "_merge_entities")
    def test_sync_alerts(self, _merge_entities):
        """[Sync] Test sync alerts"""

        feed = models.Feed()
        feed.system = models.System(id=self.SYSTEM_ID, pk=self.SYSTEM_PK)
        feed.system.routes = [
            models.Route(id=self.ROUTE_ID_1),
            models.Route(id=self.ROUTE_ID_2),
        ]
        feed_update = models.FeedUpdate(feed)

        alerts = [
            models.Alert(id=self.ID_1, route_ids=[self.ROUTE_ID_1]),
            models.Alert(id=self.ID_2, agency_ids=[self.ROUTE_ID_1]),
        ]

        persisted_alerts = [models.Alert(id=self.ID_1), models.Alert(id=self.ID_2)]
        _merge_entities.return_value = persisted_alerts

        sync._sync_alerts(feed_update, alerts)

        self.assertEqual([feed.system.routes[0]], persisted_alerts[0].routes)
        self.assertEqual([], persisted_alerts[1].routes)

        self.assertEqual(None, persisted_alerts[0].system_pk)
        self.assertEqual(self.SYSTEM_PK, persisted_alerts[1].system_pk)


class TestSyncTrips(testutil.TestCase(sync)):

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
        self.feed_update = models.FeedUpdate(models.Feed())
        self.feed_update.feed.system = self.system
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

        self.dbconnection = self.mockImportedModule(sync.dbconnection)
        self.session = mock.MagicMock()
        self.dbconnection.get_session.return_value = self.session
        self.tripdam = self.mockImportedModule(sync.tripdam)
        self.stopdam = self.mockImportedModule(sync.stopdam)
        self.scheduledam = self.mockImportedModule(sync.scheduledam)
        self.routedam = self.mockImportedModule(sync.routedam)
        self.routedam.get_id_to_pk_map_in_system.return_value = {
            self.ROUTE_1_ID: self.ROUTE_1_PK,
            self.ROUTE_2_ID: self.ROUTE_2_PK,
        }
        self.routedam.list_all_in_system.return_value = [self.route_1, self.route_2]
        self.servicemapmanager = self.mockImportedModule(sync.servicemapmanager)

    def test_sync_trips_in_route__new_trip(self):
        """[Trip updater] Sync trips in routes - new trip"""
        self.tripdam.list_all_in_system.return_value = []

        stop_id_to_stop_pk = {stop_id: int(stop_id) for stop_id in self.STOP_IDS}
        # Make the first stop invalid
        del stop_id_to_stop_pk[self.STOP_IDS[0]]
        self.stopdam.get_id_to_pk_map_in_system.return_value = stop_id_to_stop_pk

        sync._sync_trips(self.feed_update, [self.trip_1])

        self.assertEqual(
            [int(self.STOP_IDS[1]), int(self.STOP_IDS[2])],
            [stop_time.stop_pk for stop_time in self.trip_1.stop_times],
        )

    def test_sync_trips_in_route__no_more_trips(self):
        """[Trip updater] Sync trips in routes - no more trips anymore"""
        self.tripdam.list_all_in_system.return_value = [self.trip_1]

        sync._sync_trips(self.feed_update, [])

    def test_sync_trips_in_route__still_no_trips(self):
        """[Trip updater] Sync trips in routes - still no trips"""
        self.tripdam.list_all_in_system.return_value = []

        sync._sync_trips(self.feed_update, [])

    @mock.patch.object(sync, "_trigger_service_map_calculations")
    def test_sync_trips_in_route__updated_trip_same_map(self, __):
        """[Trip updater] Sync trips in routes - updated trip, same map"""

        self.tripdam.list_all_from_feed.return_value = [self.trip_1]

        stop_id_to_stop_pk = {stop_id: int(stop_id) for stop_id in self.STOP_IDS}
        self.stopdam.get_id_to_pk_map_in_system.return_value = stop_id_to_stop_pk

        feed_trip = models.Trip(id=self.TRIP_ID, route_id=self.ROUTE_1_ID)
        feed_trip.stop_times = [
            models.TripStopTime(stop_id=self.STOP_IDS[1], stop_sequence=1),
            models.TripStopTime(stop_id=self.STOP_IDS[2], stop_sequence=2),
        ]

        sync._sync_trips(self.feed_update, [feed_trip])

        self.assertEqual(
            [int(self.STOP_IDS[0]), int(self.STOP_IDS[1]), int(self.STOP_IDS[2])],
            [stop_time.stop_pk for stop_time in feed_trip.stop_times],
        )
        self.assertFalse(feed_trip.stop_times[0].future)

    @mock.patch.object(sync, "_trigger_service_map_calculations")
    def test_sync_trips_in_route__updated_trip_new_map(self, __):
        """[Trip updater] Sync trips in routes - update trip new map"""

        self.tripdam.list_all_from_feed.return_value = [self.trip_1]

        stop_id_to_stop_pk = {
            stop_id: int(stop_id)
            for stop_id in set(self.STOP_IDS).union(self.STOP_IDS_2)
        }
        self.stopdam.get_id_to_pk_map_in_system.return_value = stop_id_to_stop_pk
        feed_trip = models.Trip(id=self.TRIP_ID, route_id=self.ROUTE_1_ID)
        feed_trip.stop_times = [
            models.TripStopTime(stop_id=self.STOP_IDS[1], stop_sequence=1),
            models.TripStopTime(stop_id=self.STOP_IDS_2[2], stop_sequence=2),
        ]

        sync._sync_trips(self.feed_update, [feed_trip])

        self.assertEqual(
            [int(self.STOP_IDS[0]), int(self.STOP_IDS[1]), int(self.STOP_IDS_2[2])],
            [stop_time.stop_pk for stop_time in feed_trip.stop_times],
        )
        self.assertFalse(feed_trip.stop_times[0].future)

    @mock.patch.object(sync, "_calculate_changed_route_pks")
    def test_trigger_service_map_calculations(self, _calculate_changed_routes):
        """[Sync] Trigger service map calculations"""

        route_1_pk = 1
        route_2_pk = 2
        routes = [models.Route(pk=route_1_pk), models.Route(pk=route_2_pk)]

        _calculate_changed_routes.return_value = [route_1_pk]

        sync._trigger_service_map_calculations(mock.Mock(), mock.Mock(), routes)

        self.servicemapmanager.assert_has_calls(
            [mock.call.calculate_realtime_service_map_for_route(routes[0])]
        )

    def test_calculate_changed_route_pks__same_trip(self):
        """[Sync] Calculate changed routes - same trip"""
        self.assertEqual(
            set(),
            sync._calculate_changed_route_pks(
                [self._create_trip(1, True, [1, 2, 3])],
                [self._create_trip(1, True, [1, 2, 3])],
            ),
        )

    def test_calculate_changed_route_pks__same_trip_reversed(self):
        """[Sync] Calculate changed routes - same trip reversed"""
        self.assertEqual(
            set(),
            sync._calculate_changed_route_pks(
                [self._create_trip(1, True, [1, 2, 3])],
                [self._create_trip(1, False, [3, 2, 1])],
            ),
        )

    def test_calculate_changed_route_pks__same_trip_changed_route(self):
        """[Sync] Calculate changed routes - same trip changed route"""
        self.assertEqual(
            {1},
            sync._calculate_changed_route_pks(
                [self._create_trip(1, True, [1, 2, 3])],
                [self._create_trip(1, True, [4, 5])],
            ),
        )

    def test_calculate_changed_route_pks__different_route(self):
        """[Sync] Calculate changed routes - same trip different route"""
        self.assertEqual(
            {1, 2},
            sync._calculate_changed_route_pks(
                [self._create_trip(1, True, [1, 2, 3])],
                [self._create_trip(2, True, [1, 2, 3])],
            ),
        )

    def test_calculate_changed_route_pks__multiple_trips(self):
        """[Sync] Calculate changed routes - multiple trips"""
        self.assertEqual(
            set(),
            sync._calculate_changed_route_pks(
                [
                    self._create_trip(1, True, [1, 2, 3]),
                    self._create_trip(1, True, [5, 2, 3]),
                ],
                [
                    self._create_trip(1, False, [3, 2, 1]),
                    self._create_trip(1, False, [3, 2, 5]),
                ],
            ),
        )

    @staticmethod
    def _create_trip(route_pk, direction_id, stop_pks):
        trip = models.Trip(route_pk=route_pk, direction_id=direction_id)
        trip.stop_times = [models.TripStopTime(stop_pk=stop_pk) for stop_pk in stop_pks]
        return trip
