import unittest
import unittest.mock as mock

from transiter import models
from transiter.services import routeservice


class TestRouteService(unittest.TestCase):

    SYSTEM_ID = '1'
    ROUTE_ONE_PK = 2
    ROUTE_ONE_ID = '3'
    ROUTE_ONE_STATUS = routeservice.Status.PLANNED_SERVICE_CHANGE
    ROUTE_TWO_PK = 4
    ROUTE_TWO_ID = '5'
    ROUTE_TWO_STATUS = routeservice.Status.GOOD_SERVICE

    RAW_FREQUENCY = 700

    @classmethod
    def setUp(cls):
        cls.route_one = models.Route()
        cls.route_one.id = cls.ROUTE_ONE_ID
        cls.route_one.pk = cls.ROUTE_ONE_PK
        cls.route_one.service_patterns = []
        cls.route_one.alerts = []

        cls.route_two = models.Route()
        cls.route_two.id = cls.ROUTE_TWO_ID
        cls.route_two.pk = cls.ROUTE_TWO_PK

    @mock.patch('transiter.services.routeservice._construct_route_pk_to_status_map')
    @mock.patch('transiter.services.routeservice.routedam')
    @mock.patch('transiter.services.routeservice.systemdam')
    def test_list_all_in_system(self, systemdam, routedam,
                                _construct_route_pk_to_status_map):
        """[Route service] List all routes in a system"""

        _construct_route_pk_to_status_map.return_value = {
            self.ROUTE_ONE_PK: self.ROUTE_ONE_STATUS,
            self.ROUTE_TWO_PK: self.ROUTE_TWO_STATUS
        }
        routedam.list_all_in_system.return_value = [
            self.route_one,
            self.route_two
        ]
        systemdam.get_by_id.return_value = models.System()

        expected = [
            {
                **self.route_one.short_repr(),
                'status': self.ROUTE_ONE_STATUS
            },
            {
                **self.route_two.short_repr(),
                'status': self.ROUTE_TWO_STATUS
            }
        ]

        actual = routeservice.list_all_in_system(self.SYSTEM_ID)

        self.assertEqual(actual, expected)

        routedam.list_all_in_system.assert_called_once_with(self.SYSTEM_ID)

    @mock.patch('transiter.services.routeservice._construct_route_status')
    @mock.patch('transiter.services.routeservice.routedam')
    def test_get_in_system_by_id(self, routedam, _construct_route_status):
        """[Route service] Get a specific route in a system"""

        _construct_route_status.return_value = self.ROUTE_ONE_STATUS
        routedam.get_in_system_by_id.return_value = self.route_one
        routedam.calculate_frequency.return_value = self.RAW_FREQUENCY

        expected = {
            **self.route_one.short_repr(),
            'frequency': int(self.RAW_FREQUENCY/6)/10,
            'status': self.ROUTE_ONE_STATUS,
            'alerts': [],
            'service_maps': []
        }

        actual = routeservice.get_in_system_by_id(
            self.SYSTEM_ID,
            self.ROUTE_ONE_ID
        )

        self.assertDictEqual(actual, expected)

        routedam.get_in_system_by_id.assert_called_once_with(
            self.SYSTEM_ID,
            self.ROUTE_ONE_ID
        )

    @mock.patch('transiter.services.routeservice._construct_route_pk_to_status_map')
    def test_construct_route_status(self, _construct_route_pk_to_status_map):

        _construct_route_pk_to_status_map.return_value = {
            self.ROUTE_ONE_PK: self.ROUTE_ONE_STATUS
        }

        self.assertEqual(
            self.ROUTE_ONE_STATUS,
            routeservice._construct_route_status(self.ROUTE_ONE_PK)
        )




