from transiter.data.dams import scheduledam
from . import dbtestutil, testdata


class TestScheduleDAM(dbtestutil.TestCase):
    def test_get_scheduled_trip_pk_to_path_in_system(self):
        """[Schedule DAM] Get scheduled trip to path in system"""
        expected = {
            testdata.SCHEDULED_TRIP_1_1_PK: [
                stop.pk for stop in testdata.SCHEDULED_TRIP_1_1_STOPS
            ]
        }

        actual = scheduledam.get_scheduled_trip_pk_to_path_in_system(
            testdata.SYSTEM_ONE_PK
        )

        self.assertEqual(expected, actual)

    def test_list_scheduled_trips_with_times_in_system(self):
        """[Schedule DAM] List scheduled trips with stops in system"""
        expected = [
            (
                testdata.scheduled_trip_1_1,
                testdata.SCHEDULED_TRIP_1_1_TIMES[0],
                testdata.SCHEDULED_TRIP_1_1_TIMES[-1],
            )
        ]

        actual = scheduledam.list_scheduled_trips_with_times_in_system(
            testdata.SYSTEM_ONE_PK
        )

        self.assertEqual(expected, actual)
