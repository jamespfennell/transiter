import unittest

from transiter import models, exceptions
from transiter.services import routeservice, links
from .. import testutil


class TestRouteService(testutil.TestCase(routeservice), unittest.TestCase):

    SYSTEM_ID = "1"

    ROUTE_ONE_PK = 2
    ROUTE_ONE_ID = "3"
    ROUTE_ONE_STATUS = routeservice.Status.PLANNED_SERVICE_CHANGE

    ROUTE_TWO_PK = 4
    ROUTE_TWO_ID = "5"
    ROUTE_TWO_STATUS = routeservice.Status.GOOD_SERVICE

    RAW_FREQUENCY = 700

    SERVICE_MAP_ONE_GROUP_ID = "1000"
    SERVICE_MAP_TWO_GROUP_ID = "1001"
    STOP_ID = "1002"

    def setUp(self):
        self.route_one = models.Route()
        self.route_one.id = self.ROUTE_ONE_ID
        self.route_one.pk = self.ROUTE_ONE_PK
        self.route_one.service_patterns = []
        self.route_one.alerts = []

        self.route_two = models.Route()
        self.route_two.id = self.ROUTE_TWO_ID
        self.route_two.pk = self.ROUTE_TWO_PK

        self.service_map_one_group = models.ServiceMapGroup()
        self.service_map_one_group.id = self.SERVICE_MAP_ONE_GROUP_ID

        self.service_map_two_group = models.ServiceMapGroup()
        self.service_map_two_group.id = self.SERVICE_MAP_TWO_GROUP_ID

        self.stop = models.Stop()
        self.stop.id = self.STOP_ID
        vertex = models.ServiceMapVertex()
        vertex.stop = self.stop
        self.service_map_one = models.ServiceMap()
        self.service_map_one.vertices = [vertex]

        self.alert = models.Alert()

        self.routedam = self.mockImportedModule(routeservice.routedam)
        self.systemdam = self.mockImportedModule(routeservice.systemdam)
        self.servicemapdam = self.mockImportedModule(routeservice.servicemapdam)

    def test_list_all_in_system__system_not_found(self):
        """[Route service] List all routes in a system - system not found"""
        self.systemdam.get_by_id.return_value = None

        self.assertRaises(
            exceptions.IdNotFoundError,
            lambda: routeservice.list_all_in_system(self.SYSTEM_ID),
        )

    @testutil.patch_function(routeservice._construct_route_pk_to_status_map)
    def test_list_all_in_system(self, _construct_route_pk_to_status_map):
        """[Route service] List all routes in a system"""

        _construct_route_pk_to_status_map.return_value = {
            self.ROUTE_ONE_PK: self.ROUTE_ONE_STATUS,
            self.ROUTE_TWO_PK: self.ROUTE_TWO_STATUS,
        }
        self.routedam.list_all_in_system.return_value = [self.route_one, self.route_two]
        self.systemdam.get_by_id.return_value = models.System()

        expected = [
            {
                **self.route_one.short_repr(),
                "status": self.ROUTE_ONE_STATUS,
                "href": links.RouteEntityLink(self.route_one),
            },
            {
                **self.route_two.short_repr(),
                "status": self.ROUTE_TWO_STATUS,
                "href": links.RouteEntityLink(self.route_two),
            },
        ]

        actual = routeservice.list_all_in_system(self.SYSTEM_ID, return_links=True)

        self.assertEqual(actual, expected)

        self.routedam.list_all_in_system.assert_called_once_with(self.SYSTEM_ID)

    def test_get_in_system_by_id__route_not_found(self):
        """[Route service] Get a specific route in a system - route not found"""
        self.routedam.get_in_system_by_id.return_value = None

        self.assertRaises(
            exceptions.IdNotFoundError,
            lambda: routeservice.get_in_system_by_id(self.SYSTEM_ID, self.ROUTE_ONE_ID),
        )

    @testutil.patch_function(routeservice._construct_route_status)
    def test_get_in_system_by_id(self, _construct_route_status):
        """[Route service] Get a specific route in a system"""

        _construct_route_status.return_value = self.ROUTE_ONE_STATUS
        self.routedam.get_in_system_by_id.return_value = self.route_one
        self.routedam.calculate_periodicity.return_value = self.RAW_FREQUENCY
        self.servicemapdam.list_groups_and_maps_for_stops_in_route.return_value = [
            [self.service_map_one_group, self.service_map_one],
            [self.service_map_two_group, None],
        ]

        expected = {
            **self.route_one.long_repr(),
            "periodicity": int(self.RAW_FREQUENCY / 6) / 10,
            "status": self.ROUTE_ONE_STATUS,
            "alerts": [],
            "service_maps": [
                {
                    "group_id": self.SERVICE_MAP_ONE_GROUP_ID,
                    "stops": [
                        {
                            **self.stop.short_repr(),
                            "href": links.StopEntityLink(self.stop),
                        }
                    ],
                },
                {"group_id": self.SERVICE_MAP_TWO_GROUP_ID, "stops": []},
            ],
        }

        actual = routeservice.get_in_system_by_id(
            self.SYSTEM_ID, self.ROUTE_ONE_ID, return_links=True
        )

        self.maxDiff = None
        self.assertDictEqual(actual, expected)

        self.routedam.get_in_system_by_id.assert_called_once_with(
            self.SYSTEM_ID, self.ROUTE_ONE_ID
        )

    @testutil.patch_function(routeservice._construct_route_pk_to_status_map)
    def test_construct_route_status(self, _construct_route_pk_to_status_map):
        """[Route service] Construct a single route status"""

        _construct_route_pk_to_status_map.return_value = {
            self.ROUTE_ONE_PK: self.ROUTE_ONE_STATUS
        }

        self.assertEqual(
            self.ROUTE_ONE_STATUS,
            routeservice._construct_route_status(self.ROUTE_ONE_PK),
        )

    def test_construct_route_statuses__no_service(self):
        """[Route service] Construct route status - NO_SERVICE"""
        self._test_construct_route_statuses_runner(
            routeservice.Status.NO_SERVICE, [], False
        )

    def test_construct_route_statuses__good_service(self):
        """[Route service] Construct route status - GOOD_SERVICE"""
        self._test_construct_route_statuses_runner(
            routeservice.Status.GOOD_SERVICE, [], True
        )

    def test_construct_route_statuses__planned_service_change(self):
        """[Route service] Construct route status - PLANNED_SERVICE_CHANGE"""
        self.alert.cause = self.alert.Cause.MAINTENANCE
        self.alert.effect = self.alert.Effect.MODIFIED_SERVICE
        self._test_construct_route_statuses_runner(
            routeservice.Status.PLANNED_SERVICE_CHANGE, [self.alert], True
        )

    def test_construct_route_statuses__unplanned_service_change(self):
        """[Route service] Construct route status - UNPLANNED_SERVICE_CHANGE"""
        self.alert.cause = self.alert.Cause.ACCIDENT
        self.alert.effect = self.alert.Effect.MODIFIED_SERVICE
        self._test_construct_route_statuses_runner(
            routeservice.Status.UNPLANNED_SERVICE_CHANGE, [self.alert], True
        )

    def test_construct_route_statuses__delays(self):
        """[Route service] Construct route status - DELAYS"""
        self.alert.effect = self.alert.Effect.SIGNIFICANT_DELAYS
        self._test_construct_route_statuses_runner(
            routeservice.Status.DELAYS, [self.alert], True
        )

    def _test_construct_route_statuses_runner(
        self, expected_status, alerts, current_service
    ):

        self.routedam.get_route_pk_to_highest_priority_alerts_map.return_value = {
            self.ROUTE_ONE_PK: alerts
        }
        if current_service and len(alerts) == 0:
            self.routedam.list_route_pks_with_current_service.return_value = [
                self.ROUTE_ONE_PK
            ]
        else:
            self.routedam.list_route_pks_with_current_service.return_value = []

        expected = {self.ROUTE_ONE_PK: expected_status}

        actual = routeservice._construct_route_pk_to_status_map([self.ROUTE_ONE_PK])

        self.assertDictEqual(expected, actual)

        self.routedam.get_route_pk_to_highest_priority_alerts_map.assert_called_once()
        self.routedam.list_route_pks_with_current_service.assert_called_once_with(
            {self.ROUTE_ONE_PK} if len(alerts) == 0 else set()
        )
