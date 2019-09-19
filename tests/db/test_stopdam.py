from transiter.data.dams import stopdam
from . import dbtestutil, testdata


class TestStopDAM(dbtestutil.TestCase):
    def test_list_all_in_system(self):
        """[Stop DAM] List all in system"""
        self.assertListEqual(
            [
                testdata.stop_one,
                testdata.stop_two,
                testdata.stop_three,
                testdata.stop_four,
                testdata.stop_five,
                testdata.station_1,
                testdata.station_2,
            ],
            stopdam.list_all_in_system(testdata.SYSTEM_ONE_ID),
        )

    def test__routedata__get_in_system_by_id(self):
        """[Stop DAM] Get in system by ID"""
        self.assertEqual(
            testdata.stop_one,
            stopdam.get_in_system_by_id(testdata.SYSTEM_ONE_ID, testdata.STOP_ONE_ID),
        )

    def test__stopdata__get_id_to_pk_map_in_system(self):
        """[Stop DAM] Get ID to PK map"""
        expected = {
            testdata.STOP_ONE_ID: testdata.STOP_ONE_PK,
            testdata.STOP_TWO_ID: testdata.STOP_TWO_PK,
            "unknown": None,
        }

        actual = stopdam.get_id_to_pk_map_in_system(
            testdata.SYSTEM_ONE_ID, expected.keys()
        )

        self.assertDictEqual(expected, actual)

    def test__stopdata__list_stop_time_updates_at_stops(self):
        """[Stop DAM] List TripStopTimes at stops"""

        data = stopdam.list_stop_time_updates_at_stops([testdata.STOP_FOUR_PK])

        self.assertEqual(
            [testdata.trip_one, testdata.trip_two, testdata.trip_three],
            [stop_event.trip for stop_event in data],
        )

    def test_list_stop_time_updates_at_stops__some_past(self):
        """[Stop DAM] List TripStopTimes at stops - some past"""
        for stop_time in testdata.trip_one.stop_times:
            stop_time.future = False
        self.session.merge(testdata.trip_one)
        self.session.flush()

        data = stopdam.list_stop_time_updates_at_stops([testdata.STOP_FOUR_PK])

        self.assertEqual(
            [testdata.trip_two, testdata.trip_three],
            [stop_event.trip for stop_event in data],
        )

    def test_get_stop_pk_to_station_pk(self):
        """[Stop DAM] Get stop PK to station PK map"""
        expected = {
            testdata.STOP_ONE_PK: testdata.STATION_1_PK,
            testdata.STOP_TWO_PK: testdata.STATION_1_PK,
            testdata.STOP_THREE_PK: testdata.STOP_THREE_PK,
            testdata.STOP_FOUR_PK: testdata.STOP_FOUR_PK,
            testdata.STOP_FIVE_PK: testdata.STOP_FIVE_PK,
            testdata.STATION_1_PK: testdata.STATION_1_PK,
            testdata.STATION_2_PK: testdata.STATION_2_PK,
        }

        actual = stopdam.get_stop_pk_to_station_pk_map_in_system(testdata.SYSTEM_ONE_ID)

        self.assertDictEqual(expected, actual)
