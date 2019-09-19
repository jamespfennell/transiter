from transiter.data.dams import tripdam
from . import dbtestutil, testdata


class TestTripDAM(dbtestutil.TestCase):
    def test__trip_dao__list_all_in_route(self):
        """[Trip DAM] List all in route"""
        self.assertEqual(
            [testdata.trip_one, testdata.trip_two, testdata.trip_three],
            tripdam.list_all_in_route_by_pk(testdata.ROUTE_ONE_PK),
        )

    def test__trip_dao__list_all_in_route__no_trips(self):
        """[Trip DAM] List all in route"""
        self.assertEqual([], tripdam.list_all_in_route_by_pk(testdata.ROUTE_TWO_PK))

    def test_get_in_route_by_id(self):
        """[Trip DAM] Get in route by ID"""
        self.assertEqual(
            testdata.trip_three,
            tripdam.get_in_route_by_id(
                testdata.SYSTEM_ONE_ID, testdata.ROUTE_ONE_ID, testdata.TRIP_THREE_ID
            ),
        )

    def test_get_in_route_by_id__no_system(self):
        """[Trip DAM] Get in route by ID - unknown system"""
        self.assertEqual(
            None,
            tripdam.get_in_route_by_id(
                "fake_id", testdata.ROUTE_ONE_ID, testdata.TRIP_THREE_ID
            ),
        )

    def test_get_in_route_by_id__no_route(self):
        """[Trip DAM] Get in route by ID - unknown route"""
        self.assertEqual(
            None,
            tripdam.get_in_route_by_id(
                testdata.SYSTEM_ONE_ID, "fake_id", testdata.TRIP_THREE_ID
            ),
        )

    def test_get_trip_pk_to_last_stop_map(self):
        """[Trip DAM] Get trip PK to last stop map"""
        expected = {
            testdata.TRIP_ONE_PK: testdata.stop_four,
            testdata.TRIP_TWO_PK: testdata.stop_four,
            testdata.TRIP_THREE_PK: testdata.stop_four,
        }

        actual = tripdam.get_trip_pk_to_last_stop_map(expected.keys())

        self.assertEqual(expected, actual)

    def test_get_trip_pk_to_path_map(self):
        """[Trip DAM] Get trip PK to path map"""
        expected = {
            testdata.TRIP_ONE_PK: [stop.pk for stop in testdata.TRIP_ONE_PATH],
            testdata.TRIP_TWO_PK: [stop.pk for stop in testdata.TRIP_TWO_PATH],
            testdata.TRIP_THREE_PK: [stop.pk for stop in testdata.TRIP_THREE_PATH],
        }

        actual = tripdam.get_trip_pk_to_path_map(testdata.ROUTE_ONE_PK)

        self.assertEqual(expected, actual)
