import datetime
import io
import unittest
import zipfile
from unittest import mock

from transiter import models
from transiter.services.update import gtfsstaticparser
from ... import testutil


class TestGtfsStaticUtil(testutil.TestCase(gtfsstaticparser), unittest.TestCase):
    ROUTE_ID = "L"
    ROUTE_COLOR = "red"
    ROUTE_DESCRIPTION = "All times"

    STOP_ID = "N1"
    STOP_NAME = "This stop"
    STOP_ID_2 = "N2"
    STOP_NAME_2 = "This stop 2"
    STOP_LON = "3"
    STOP_LAT = "4"

    SERVICE_ID = "M"
    TRIP_ID = "Z"

    def setUp(self):
        self.GtfsStaticFile = self.mockModuleAttribute("GtfsStaticFile")

    def test_parse(self):
        binary_content = mock.MagicMock()

        parse_routes = self.mockModuleAttribute("parse_routes")
        parse_routes.return_value = [1]
        parse_stops = self.mockModuleAttribute("parse_stops")
        parse_stops.return_value = [2]
        parse_schedule = self.mockModuleAttribute("parse_schedule")
        parse_schedule.return_value = [3]

        gtfs_static_file = mock.MagicMock()
        self.GtfsStaticFile.return_value = gtfs_static_file

        self.assertEqual(
            [1, 2, 3], list(gtfsstaticparser.parse_gtfs_static(binary_content))
        )

        self.GtfsStaticFile.assert_called_once_with(binary_content)
        parse_routes.assert_called_once_with(gtfs_static_file)
        parse_stops.assert_called_once_with(gtfs_static_file)
        parse_schedule.assert_called_once_with(gtfs_static_file)

    def test_parse_routes(self):
        gtfs_static_file = mock.Mock()
        gtfs_static_file.routes.return_value = [
            {
                "route_id": self.ROUTE_ID,
                "route_color": self.ROUTE_COLOR,
                "route_desc": self.ROUTE_DESCRIPTION,
                "route_type": models.Route.Type.RAIL.value,
            }
        ]

        expected_route = models.Route(
            id=self.ROUTE_ID,
            color=self.ROUTE_COLOR,
            description=self.ROUTE_DESCRIPTION,
            text_color="000000",
            type=models.Route.Type.RAIL,
        )

        self.assertEqual(
            list(gtfsstaticparser.parse_routes(gtfs_static_file)), [expected_route]
        )

    @mock.patch.object(gtfsstaticparser, "create_station_from_child_stops")
    def test_parse_stops__single_stop(self, create_station):
        """[GTFS Static Util] Parse stops - single stop"""
        gtfs_static_file = mock.Mock()
        gtfs_static_file.stops.return_value = [
            {
                "stop_id": self.STOP_ID,
                "stop_name": self.STOP_NAME,
                "stop_lon": self.STOP_LON,
                "stop_lat": self.STOP_LAT,
                "location_type": "0",
            }
        ]
        gtfs_static_file.transfers.return_value = []

        expected_stop = models.Stop(
            id=self.STOP_ID,
            name=self.STOP_NAME,
            longitude=self.STOP_LON,
            latitude=self.STOP_LAT,
            is_station=True,
        )

        self.assertEqual(
            list(gtfsstaticparser.parse_stops(gtfs_static_file)), [expected_stop]
        )

    @mock.patch.object(gtfsstaticparser, "create_station_from_child_stops")
    def test_parse_stops__parent_and_child_stop(self, create_station):
        """[GTFS Static Util] Parse stops - parent and child stop"""
        gtfs_static_file = mock.Mock()
        gtfs_static_file.stops.return_value = [
            {
                "stop_id": self.STOP_ID,
                "stop_name": self.STOP_NAME,
                "stop_lon": self.STOP_LON,
                "stop_lat": self.STOP_LAT,
                "location_type": "0",
                "parent_station": self.STOP_ID_2,
            },
            {
                "stop_id": self.STOP_ID_2,
                "stop_name": self.STOP_NAME_2,
                "stop_lon": self.STOP_LON,
                "stop_lat": self.STOP_LAT,
                "location_type": "1",
                "parent_station": None,
            },
        ]
        gtfs_static_file.transfers.return_value = []

        expected_stop_1 = models.Stop(
            id=self.STOP_ID,
            name=self.STOP_NAME,
            longitude=self.STOP_LON,
            latitude=self.STOP_LAT,
            is_station=False,
        )
        expected_stop_2 = models.Stop(
            id=self.STOP_ID_2,
            name=self.STOP_NAME_2,
            longitude=self.STOP_LON,
            latitude=self.STOP_LAT,
            is_station=True,
        )

        actual_stops = list(gtfsstaticparser.parse_stops(gtfs_static_file))

        self.assertEqual([expected_stop_1, expected_stop_2], actual_stops)
        self.assertEqual(expected_stop_2, actual_stops[0].parent_stop)

    @mock.patch.object(gtfsstaticparser, "create_station_from_child_stops")
    def test_parse_stops__siblings_by_transfer(self, create_station):
        """[GTFS Static Util] Parse stops - parent and child stop"""
        gtfs_static_file = mock.Mock()
        gtfs_static_file.stops.return_value = [
            {
                "stop_id": self.STOP_ID,
                "stop_name": self.STOP_NAME,
                "stop_lon": self.STOP_LON,
                "stop_lat": self.STOP_LAT,
                "location_type": "1",
            },
            {
                "stop_id": self.STOP_ID_2,
                "stop_name": self.STOP_NAME_2,
                "stop_lon": self.STOP_LON,
                "stop_lat": self.STOP_LAT,
                "location_type": "1",
            },
        ]
        gtfs_static_file.transfers.return_value = [
            {"from_stop_id": self.STOP_ID, "to_stop_id": self.STOP_ID_2},
            {"from_stop_id": self.STOP_ID, "to_stop_id": self.STOP_ID},
        ]

        expected_stop_1 = models.Stop(
            id=self.STOP_ID,
            name=self.STOP_NAME,
            longitude=self.STOP_LON,
            latitude=self.STOP_LAT,
            is_station=True,
        )
        expected_stop_2 = models.Stop(
            id=self.STOP_ID_2,
            name=self.STOP_NAME_2,
            longitude=self.STOP_LON,
            latitude=self.STOP_LAT,
            is_station=True,
        )
        expected_station = models.Stop(id="FakeID")
        create_station.return_value = expected_station

        actual_stops = list(gtfsstaticparser.parse_stops(gtfs_static_file))

        self.assertEqual(
            [expected_stop_1, expected_stop_2, expected_station], actual_stops
        )
        self.assertEqual(expected_station, actual_stops[0].parent_stop)
        self.assertEqual(expected_station, actual_stops[1].parent_stop)

    def test_create_station_from_child_stops(self):
        """[GTFS Static Util] Create parent from child stops"""

        child_1 = models.Stop(id="A", name="Name 1", latitude=4, longitude=1)
        child_2 = models.Stop(id="B", name="Name 1", latitude=1, longitude=1)
        child_3 = models.Stop(id="C", name="Name 2", latitude=1, longitude=1)

        expected_station = models.Stop(
            id="A-B-C", name="Name 1", latitude=2, longitude=1, is_station=True
        )

        actual_station = gtfsstaticparser.create_station_from_child_stops(
            [child_1, child_2, child_3]
        )

        self.assertEqual(expected_station, actual_station)

    def test_create_station_from_child_stops_hybrid_name(self):
        """[GTFS Static Util] Create parent from child stops - hybrid name"""

        child_1 = models.Stop(id="A", name="Name 1", latitude=3, longitude=1)
        child_2 = models.Stop(id="B", name="Name 2", latitude=1, longitude=1)

        expected_station = models.Stop(
            id="A-B", name="Name 1 / Name 2", latitude=2, longitude=1, is_station=True
        )

        actual_station = gtfsstaticparser.create_station_from_child_stops(
            [child_1, child_2]
        )

        self.assertEqual(expected_station, actual_station)

    def test_create_station_from_child_stops_substring_case(self):
        """[GTFS Static Util] Create parent from child stops - substring name case"""

        child_1 = models.Stop(id="A", name="Name 1", latitude=3, longitude=1)
        child_2 = models.Stop(id="B", name="Name 1 (and more)", latitude=1, longitude=1)

        expected_station = models.Stop(
            id="A-B", name="Name 1 (and more)", latitude=2, longitude=1, is_station=True
        )

        actual_station = gtfsstaticparser.create_station_from_child_stops(
            [child_1, child_2]
        )

        self.assertEqual(expected_station, actual_station)

    def test_parse_services(self):
        """[GTFS static util] Parse services"""

        gtfs_static_file = mock.Mock()

        gtfs_static_file.calendar.return_value = [
            {
                "service_id": self.SERVICE_ID,
                "monday": "1",
                "tuesday": "1",
                "wednesday": "1",
                "thursday": "0",
                "friday": "0",
                "saturday": "0",
                "sunday": "0",
            }
        ]
        service = models.ScheduledService(
            id=self.SERVICE_ID,
            monday=True,
            tuesday=True,
            wednesday=True,
            thursday=False,
            friday=False,
            saturday=False,
            sunday=False,
        )

        gtfs_static_file.trips.return_value = [
            {
                "service_id": self.SERVICE_ID,
                "trip_id": self.TRIP_ID,
                "route_id": self.ROUTE_ID,
                "direction_id": "1",
            },
            {
                "service_id": "Unknown service ID",
                "trip_id": self.TRIP_ID,
                "route_id": self.ROUTE_ID,
                "direction_id": "1",
            },
        ]
        trip = models.ScheduledTrip(id=self.TRIP_ID, direction_id=True)

        gtfs_static_file.stop_times.return_value = [
            {
                "trip_id": self.TRIP_ID,
                "stop_id": self.STOP_ID,
                "stop_sequence": "1",
                "departure_time": "11:12:13",
                "arrival_time": "11:12:13",
            },
            {
                "trip_id": "Unknown trip ID",
                "stop_id": self.STOP_ID_2,
                "stop_sequence": "1",
                "departure_time": "11:12:13",
                "arrival_time": "11:12:13",
            },
        ]
        stop_time = models.ScheduledTripStopTimeLight()
        stop_time.stop_sequence = 1
        stop_time.stop_id = self.STOP_ID
        stop_time.departure_time = datetime.time(hour=11, minute=12, second=13)
        stop_time.arrival_time = datetime.time(hour=11, minute=12, second=13)

        actual_services = list(gtfsstaticparser.parse_schedule(gtfs_static_file))

        self.assertEqual([service], actual_services)
        self.assertEqual([trip], actual_services[0].trips)
        self.assertEqual(self.ROUTE_ID, actual_services[0].trips[0].route_id)
        self.assertEqual([stop_time], actual_services[0].trips[0].stop_times_light)


class TestReadZipFile(unittest.TestCase):

    HEADER_1 = "id"
    HEADER_2 = "name"
    VALUE_1_1 = "1"
    VALUE_1_2 = "Stop"
    VALUE_2_1 = "2"
    VALUE_2_2 = "Route"

    def test_file_exists(self):
        """[GTFS Static Util] Read Zip archive - file exists"""
        csv = """{},{}\n{},{}\n{},{}""".format(
            self.HEADER_1,
            self.HEADER_2,
            self.VALUE_1_1,
            self.VALUE_1_2,
            self.VALUE_2_1,
            self.VALUE_2_2,
        )
        expected = [
            {self.HEADER_1: self.VALUE_1_1, self.HEADER_2: self.VALUE_1_2},
            {self.HEADER_1: self.VALUE_2_1, self.HEADER_2: self.VALUE_2_2},
        ]

        file_name_to_func_name = {
            gtfsstaticparser.GtfsStaticFile._InternalFileName.CALENDAR: "calendar",
            gtfsstaticparser.GtfsStaticFile._InternalFileName.ROUTES: "routes",
            gtfsstaticparser.GtfsStaticFile._InternalFileName.STOPS: "stops",
            gtfsstaticparser.GtfsStaticFile._InternalFileName.STOP_TIMES: "stop_times",
            gtfsstaticparser.GtfsStaticFile._InternalFileName.TRANSFERS: "transfers",
            gtfsstaticparser.GtfsStaticFile._InternalFileName.TRIPS: "trips",
        }

        for file_name, func_name in file_name_to_func_name.items():
            binary_content = self._create_zip(file_name.value, csv)
            gtfs_file = gtfsstaticparser.GtfsStaticFile(binary_content)
            func = getattr(gtfs_file, func_name)
            actual = list(func())

            self.assertEqual(expected, actual)

    def test_file_does_not_exist(self):
        """[GTFS Static Util] Read Zip archive - file does not exist"""
        csv = """{},{}\n{},{}\n{},{}""".format(
            self.HEADER_1,
            self.HEADER_2,
            self.VALUE_1_1,
            self.VALUE_1_2,
            self.VALUE_2_1,
            self.VALUE_2_2,
        )
        binary_content = self._create_zip(
            gtfsstaticparser.GtfsStaticFile._InternalFileName.STOPS.value, csv
        )

        actual = list(gtfsstaticparser.GtfsStaticFile(binary_content).routes())

        self.assertEqual([], actual)

    @staticmethod
    def _create_zip(file_name, file_content):
        buff = io.BytesIO()
        zip_file = zipfile.ZipFile(buff, mode="w")
        zip_file.writestr(file_name, file_content)
        zip_file.close()
        buff.seek(0)
        return buff.read()
