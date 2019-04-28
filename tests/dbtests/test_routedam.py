import unittest

from . import dbtestutil, testdata

from transiter.data.dams import routedam


class TestRouteDAM(dbtestutil.TestCase):

    def test_list_all_in_system(self):
        """[Route DAM] List all in system"""
        self.assertListEqual(
            [testdata.route_one, testdata.route_two, testdata.route_three],
            routedam.list_all_in_system(testdata.SYSTEM_ONE_ID)
        )

    def test__routedata__get_in_system_by_id(self):
        """[Route DAM] Get in system by ID"""
        db_route = routedam.get_in_system_by_id(
            testdata.SYSTEM_ONE_ID, testdata.ROUTE_ONE_ID)

        self.assertEqual(testdata.route_one, db_route)

    def test_get_id_to_pk_map_in_system(self):
        """[Route DAM] Get ID to PK map in system"""
        expected = {
            testdata.ROUTE_ONE_ID: testdata.ROUTE_ONE_PK,
            testdata.ROUTE_TWO_ID: testdata.ROUTE_TWO_PK,
            testdata.ROUTE_THREE_ID: testdata.ROUTE_THREE_PK,
            'unknown': None,
        }

        actual = routedam.get_id_to_pk_map_in_system(
            testdata.SYSTEM_ONE_ID, expected.keys())

        self.assertEqual(expected, actual)

    def test_list_terminus_data(self):
        """[Route DAM] Calculate frequency"""
        data = routedam.calculate_frequency(testdata.ROUTE_ONE_PK)

        self.assertEqual(3600, int(data))

    def test_list_route_pks_with_current_service(self):
        """[Route DAM] List route PKs with current service"""
        self.assertEqual(
            [testdata.ROUTE_ONE_PK],
            routedam.list_route_pks_with_current_service(
                [testdata.ROUTE_ONE_PK, testdata.ROUTE_TWO_PK, testdata.ROUTE_THREE_PK]
            )
        )
