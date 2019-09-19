import datetime
import io
import unittest
import zipfile
from unittest import mock

from transiter import models
from transiter.services.update import gtfsstaticutil
from ... import testutil


class TestGtfsStaticUtil(testutil.TestCase(gtfsstaticutil), unittest.TestCase):
    SYSTEM_PK = 3
    ROUTE_PK = 101
    ROUTE_ID = "L"
    SERVICE_PK = 102
    SERVICE_ID = "M"
    STOP_ID = "N"
    STOP_PK = 103
    TRIP_ID = "Z"
    TRIP_PK = 104

    def setUp(self):
        self.zipfile = self.mockImportedModule(gtfsstaticutil.zipfile)
        self.io = self.mockImportedModule(gtfsstaticutil.io)
        self.read_gtfs_static_file = self.mockModuleAttribute("read_gtfs_static_file")
        self.routedam = self.mockImportedModule(gtfsstaticutil.routedam)
        self.stopdam = self.mockImportedModule(gtfsstaticutil.stopdam)
        self.fastoperations = self.mockImportedModule(gtfsstaticutil.fastoperations)
        self.genericqueries = self.mockImportedModule(gtfsstaticutil.genericqueries)
        self.servicemapmanager = self.mockImportedModule(
            gtfsstaticutil.servicemapmanager
        )
        self.get_id_to_pk_map = {models.ScheduledService: {}, models.ScheduledTrip: {}}
        self.genericqueries.get_id_to_pk_map = lambda model_type: self.get_id_to_pk_map[
            model_type
        ]
        self.system = models.System(pk=self.SYSTEM_PK)

    @mock.patch.object(gtfsstaticutil, "_create_station_from_child_stops")
    @mock.patch.object(gtfsstaticutil, "fast_scheduled_entities_insert")
    @mock.patch.object(gtfsstaticutil, "GtfsStaticData")
    def test_parse_gtfs_static(self, GtfsStaticData, _fast_insert, _create_station):
        """[GTFS Static Util] Parse GTFS Static"""
        feed = models.Feed(system=self.system)
        feed_update = models.FeedUpdate(feed)

        grandchild_1 = models.Stop(id="g1", parent_stop_id="c1")
        grandchild_2 = models.Stop(id="g2", parent_stop_id="c2")
        grandchild_3 = models.Stop(id="g3", parent_stop_id="c2")
        grandchild_4 = models.Stop(id="g4", parent_stop_id="c3")
        child_1 = models.Stop(id="c1")
        child_2 = models.Stop(id="c2")
        child_3 = models.Stop(id="c3")
        all_feed_stops = [
            grandchild_1,
            grandchild_2,
            grandchild_3,
            grandchild_4,
            child_1,
            child_2,
            child_3,
        ]

        parent = models.Stop()
        _create_station.return_value = parent

        route = models.Route(id="r1")

        gtfs_static_data = mock.MagicMock()
        gtfs_static_data.stop_id_to_stop = {stop.id: stop for stop in all_feed_stops}
        gtfs_static_data.route_id_to_route = {route.id: route}
        gtfs_static_data.transfer_tuples = [("c1", "c2")]
        GtfsStaticData.return_value = gtfs_static_data

        zip_data = mock.MagicMock()

        gtfsstaticutil.parse_gtfs_static(feed_update, zip_data)

        for stop in all_feed_stops:
            self.assertEqual(self.system, stop.system)
        self.assertEqual(grandchild_1.parent_stop, child_1)
        self.assertEqual(grandchild_2.parent_stop, child_2)
        self.assertEqual(grandchild_3.parent_stop, child_2)
        self.assertEqual(grandchild_4.parent_stop, child_3)

        _create_station.assert_called_once()

    def test_create_station_from_child_stops(self):
        """[GTFS Static Util] Create parent from child stops"""

        child_1 = models.Stop(id="A", name="Name 1", latitude=4, longitude=1)
        child_2 = models.Stop(id="B", name="Name 1", latitude=1, longitude=1)
        child_3 = models.Stop(id="C", name="Name 2", latitude=1, longitude=1)

        expected_station = models.Stop(
            id="A-B-C", name="Name 1", latitude=2, longitude=1, is_station=True
        )

        actual_station = gtfsstaticutil._create_station_from_child_stops(
            [child_1, child_2, child_3]
        )

        self.assertEqual(expected_station, actual_station)
        self.assertEqual(expected_station, child_1.parent_stop)
        self.assertEqual(expected_station, child_2.parent_stop)
        self.assertEqual(expected_station, child_3.parent_stop)

    def test_create_station_from_child_stops_hybrid_name(self):
        """[GTFS Static Util] Create parent from child stops - hybrid name"""

        child_1 = models.Stop(id="A", name="Name 1", latitude=3, longitude=1)
        child_2 = models.Stop(id="B", name="Name 2", latitude=1, longitude=1)

        expected_station = models.Stop(
            id="A-B", name="Name 1 / Name 2", latitude=2, longitude=1, is_station=True
        )

        actual_station = gtfsstaticutil._create_station_from_child_stops(
            [child_1, child_2]
        )

        self.assertEqual(expected_station, actual_station)
        self.assertEqual(expected_station, child_1.parent_stop)
        self.assertEqual(expected_station, child_2.parent_stop)

    def test_create_station_from_child_stops_substring_case(self):
        """[GTFS Static Util] Create parent from child stops - substring name case"""

        child_1 = models.Stop(id="A", name="Name 1", latitude=3, longitude=1)
        child_2 = models.Stop(id="B", name="Name 1 (and more)", latitude=1, longitude=1)

        expected_station = models.Stop(
            id="A-B", name="Name 1 (and more)", latitude=2, longitude=1, is_station=True
        )

        actual_station = gtfsstaticutil._create_station_from_child_stops(
            [child_1, child_2]
        )

        self.assertEqual(expected_station, actual_station)
        self.assertEqual(expected_station, child_1.parent_stop)
        self.assertEqual(expected_station, child_2.parent_stop)

    def test_parse_routes(self):
        """[GTFS static util] Parse routes"""

        data = {
            "route_id": "1",
            "route_color": "2",
            "route_url": "3",
            "route_short_name": "4",
            "route_long_name": "5",
            "route_desc": "6",
        }
        route = models.Route()
        route.id = "1"
        route.color = "2"
        route.url = "3"
        route.short_name = "4"
        route.long_name = "5"
        route.description = "6"

        self._set_gtfs_static_file_data(gtfsstaticutil.GtfsStaticFile.ROUTES, [data])

        gtfs_static_parser = gtfsstaticutil.GtfsStaticData()
        gtfs_static_parser.parse_from_zip_data(mock.MagicMock())

        self.assertEqual(gtfs_static_parser.route_id_to_route, {"1": route})

    def test_parse_stops__station(self):
        """[GTFS static util] Parse stops, station"""

        data = {
            "stop_id": "1",
            "stop_name": "2",
            "stop_lon": "3",
            "stop_lat": "4",
            "parent_station": "5",
            "location_type": "1",
        }
        stop = models.Stop()
        stop.id = "1"
        stop.name = "2"
        stop.longitude = "3"
        stop.latitude = "4"
        stop.is_station = True

        self._set_gtfs_static_file_data(gtfsstaticutil.GtfsStaticFile.STOPS, [data])

        gtfs_static_parser = gtfsstaticutil.GtfsStaticData()
        gtfs_static_parser.parse_from_zip_data(mock.MagicMock())

        self.assertEqual(gtfs_static_parser.stop_id_to_stop, {"1": stop})

    def test_parse_stops(self):
        """[GTFS static util] Parse stops, not a station"""

        data = {
            "stop_id": "1",
            "stop_name": "2",
            "stop_lon": "3",
            "stop_lat": "4",
            "parent_station": "5",
            "location_type": "0",
        }
        stop = models.Stop()
        stop.id = "1"
        stop.name = "2"
        stop.longitude = "3"
        stop.latitude = "4"
        stop.is_station = False

        self._set_gtfs_static_file_data(gtfsstaticutil.GtfsStaticFile.STOPS, [data])

        gtfs_static_parser = gtfsstaticutil.GtfsStaticData()
        gtfs_static_parser.parse_from_zip_data(mock.MagicMock())

        self.assertEqual(gtfs_static_parser.stop_id_to_stop, {"1": stop})

    def test_parse_transfers(self):
        """[GTFS static util] Parse transfers"""

        data = [
            {"from_stop_id": "1", "to_stop_id": "2"},
            {"from_stop_id": "3", "to_stop_id": "3"},
        ]

        self._set_gtfs_static_file_data(gtfsstaticutil.GtfsStaticFile.TRANSFERS, data)

        gtfs_static_parser = gtfsstaticutil.GtfsStaticData()
        gtfs_static_parser.parse_from_zip_data(mock.MagicMock())

        self.assertEqual(gtfs_static_parser.transfer_tuples, [("1", "2")])

    def test_parse_services(self):
        """[GTFS static util] Parse services"""

        raw_data = {
            "service_id": "1",
            "monday": "1",
            "tuesday": "1",
            "wednesday": "1",
            "thursday": "0",
            "friday": "0",
            "saturday": "0",
            "sunday": "0",
        }
        transformed_data = {
            "id": "1",
            "system_pk": self.SYSTEM_PK,
            "monday": True,
            "tuesday": True,
            "wednesday": True,
            "thursday": False,
            "friday": False,
            "saturday": False,
            "sunday": False,
        }

        fast_inserter = self._create_fast_inserter(models.ScheduledService)
        self._set_gtfs_static_file_data(
            gtfsstaticutil.GtfsStaticFile.CALENDAR, [raw_data]
        )

        gtfsstaticutil.fast_scheduled_entities_insert(mock.MagicMock(), self.system)

        fast_inserter.add.assert_called_once_with(transformed_data)

    def test_parse_scheduled_trips(self):
        """[GTFS static util] Parse scheduled trips"""

        raw_data = {
            "trip_id": "1",
            "direction_id": "1",
            "route_id": self.ROUTE_ID,
            "service_id": self.SERVICE_ID,
        }
        transformed_data = {
            "id": "1",
            "direction_id": True,
            "route_pk": self.ROUTE_PK,
            "service_pk": self.SERVICE_PK,
        }

        fast_inserter = self._create_fast_inserter(models.ScheduledTrip)
        self._set_gtfs_static_file_data(gtfsstaticutil.GtfsStaticFile.TRIPS, [raw_data])

        self.get_id_to_pk_map[models.ScheduledService] = {
            self.SERVICE_ID: self.SERVICE_PK
        }
        self.routedam.get_id_to_pk_map_in_system.return_value = {
            self.ROUTE_ID: self.ROUTE_PK
        }

        gtfsstaticutil.fast_scheduled_entities_insert(mock.MagicMock(), self.system)

        fast_inserter.add.assert_called_once_with(transformed_data)

    def test_parse_scheduled_trip_stop_times(self):
        """[GTFS static util] Parse scheduled trip stop times"""

        raw_data = {
            "trip_id": self.TRIP_ID,
            "stop_id": self.STOP_ID,
            "stop_sequence": "11",
            "departure_time": "02:03:04",
            "arrival_time": "16:17:18",
        }
        transformed_data = {
            "trip_pk": self.TRIP_PK,
            "stop_pk": self.STOP_PK,
            "stop_sequence": 11,
            "departure_time": datetime.time(2, 3, 4),
            "arrival_time": datetime.time(16, 17, 18),
        }

        fast_inserter = self._create_fast_inserter(models.ScheduledTripStopTime)
        self._set_gtfs_static_file_data(
            gtfsstaticutil.GtfsStaticFile.STOP_TIMES, [raw_data]
        )

        self.get_id_to_pk_map[models.ScheduledTrip] = {self.TRIP_ID: self.TRIP_PK}
        self.stopdam.get_id_to_pk_map_in_system.return_value = {
            self.STOP_ID: self.STOP_PK
        }

        gtfsstaticutil.fast_scheduled_entities_insert(mock.MagicMock(), self.system)

        fast_inserter.add.assert_called_once_with(transformed_data)

    def _create_fast_inserter(self, model_type):
        fast_inserter = mock.MagicMock()

        def FastInserter(model_type_actual):
            if model_type == model_type_actual:
                return fast_inserter
            else:
                return mock.MagicMock()

        self.fastoperations.FastInserter.side_effect = FastInserter
        return fast_inserter

    def _set_gtfs_static_file_data(self, gtfs_static_file, data):
        def read_gtfs_static_file(__, gtfs_static_file_actual):
            if gtfs_static_file == gtfs_static_file_actual:
                return data
            return []

        self.read_gtfs_static_file.side_effect = read_gtfs_static_file


class TestReadZipFile(unittest.TestCase):
    def setUp(self):
        raw_csv = """id,stop_name\n1,Stop One\n2,Stop Two"""
        buff = io.BytesIO()
        self.zip_file = zipfile.ZipFile(buff, mode="w")
        self.zip_file.writestr(gtfsstaticutil.GtfsStaticFile.STOPS.value, raw_csv)

    def test_file_exists(self):
        """[GTFS Static Util] Read Zip archive - file exists"""

        expected = [
            {"id": "1", "stop_name": "Stop One"},
            {"id": "2", "stop_name": "Stop Two"},
        ]

        actual = list(
            gtfsstaticutil.read_gtfs_static_file(
                self.zip_file, gtfsstaticutil.GtfsStaticFile.STOPS
            )
        )

        self.assertEqual(expected, actual)

    def test_file_does_not_exist(self):
        """[GTFS Static Util] Read Zip archive - file does not exist"""

        actual = list(
            gtfsstaticutil.read_gtfs_static_file(
                self.zip_file, gtfsstaticutil.GtfsStaticFile.ROUTES
            )
        )

        self.assertEqual([], actual)
