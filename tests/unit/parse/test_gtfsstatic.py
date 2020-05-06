import datetime
import io
import unittest
import zipfile
from unittest import mock

import pytest

from transiter import models, parse
from transiter.parse import gtfsstatic as gtfsstaticparser

ROUTE_ID = "L"
ROUTE_COLOR = "red"
ROUTE_DESCRIPTION = "All times"

STOP_ID = "N1"
STOP_NAME = "This stop"
STOP_ID_2 = "N2"
STOP_NAME_2 = "This stop 2"
STOP_LON = "3.67"
STOP_LAT = "4.003"

SERVICE_ID = "M"
TRIP_ID = "Z"


def test_parse_routes():
    gtfs_static_file = mock.Mock()
    gtfs_static_file.routes.return_value = [
        {
            "route_id": ROUTE_ID,
            "route_color": ROUTE_COLOR,
            "route_desc": ROUTE_DESCRIPTION,
            "route_type": models.Route.Type.RAIL.value,
        }
    ]

    expected_route = parse.Route(
        id=ROUTE_ID,
        color=ROUTE_COLOR,
        description=ROUTE_DESCRIPTION,
        text_color="000000",
        type=models.Route.Type.RAIL,
    )

    assert [expected_route] == list(gtfsstaticparser._parse_routes(gtfs_static_file))


def test_parse(monkeypatch):
    monkeypatch.setattr(gtfsstaticparser, "_parse_routes", lambda *args, **kwargs: [1])
    monkeypatch.setattr(gtfsstaticparser, "_parse_stops", lambda *args, **kwargs: [2])
    monkeypatch.setattr(
        gtfsstaticparser, "_parse_schedule", lambda *args, **kwargs: [3]
    )
    monkeypatch.setattr(gtfsstaticparser, "_GtfsStaticFile", mock.MagicMock())

    parser = gtfsstaticparser.GtfsStaticParser()
    parser.load_content(b"")

    assert [1] == list(parser.get_routes())
    assert [2] == list(parser.get_stops())
    assert [3] == list(parser.get_scheduled_services())


@pytest.fixture
def mock_create_station(monkeypatch):
    mock_create = mock.MagicMock()
    monkeypatch.setattr(
        gtfsstaticparser, "_create_station_from_child_stops", mock_create
    )
    return mock_create


def test_parse_stops__single_stop(mock_create_station):
    gtfs_static_file = mock.Mock()
    gtfs_static_file.stops.return_value = [
        {
            "stop_id": STOP_ID,
            "stop_name": STOP_NAME,
            "stop_lon": STOP_LON,
            "stop_lat": STOP_LAT,
            "location_type": "0",
        }
    ]
    gtfs_static_file.transfers.return_value = []

    expected_stop = parse.Stop(
        id=STOP_ID,
        name=STOP_NAME,
        longitude=float(STOP_LON),
        latitude=float(STOP_LAT),
        is_station=True,
    )

    assert [expected_stop] == list(gtfsstaticparser._parse_stops(gtfs_static_file))


def test_parse_stops__parent_and_child_stop(mock_create_station):
    gtfs_static_file = mock.Mock()
    gtfs_static_file.stops.return_value = [
        {
            "stop_id": STOP_ID,
            "stop_name": STOP_NAME,
            "stop_lon": STOP_LON,
            "stop_lat": STOP_LAT,
            "location_type": "0",
            "parent_station": STOP_ID_2,
        },
        {
            "stop_id": STOP_ID_2,
            "stop_name": STOP_NAME_2,
            "stop_lon": STOP_LON,
            "stop_lat": STOP_LAT,
            "location_type": "1",
            "parent_station": "",
        },
    ]
    gtfs_static_file.transfers.return_value = []

    expected_stop_2 = parse.Stop(
        id=STOP_ID_2,
        name=STOP_NAME_2,
        longitude=float(STOP_LON),
        latitude=float(STOP_LAT),
        is_station=True,
    )
    expected_stop_1 = parse.Stop(
        id=STOP_ID,
        name=STOP_NAME,
        longitude=float(STOP_LON),
        latitude=float(STOP_LAT),
        is_station=False,
        parent_stop=expected_stop_2,
    )

    actual_stops = list(gtfsstaticparser._parse_stops(gtfs_static_file))

    assert [expected_stop_1, expected_stop_2] == actual_stops


def test_parse_stops__siblings_by_transfer(mock_create_station):
    gtfs_static_file = mock.Mock()
    gtfs_static_file.stops.return_value = [
        {
            "stop_id": STOP_ID,
            "stop_name": STOP_NAME,
            "stop_lon": STOP_LON,
            "stop_lat": STOP_LAT,
            "location_type": "1",
        },
        {
            "stop_id": STOP_ID_2,
            "stop_name": STOP_NAME_2,
            "stop_lon": STOP_LON,
            "stop_lat": STOP_LAT,
            "location_type": "1",
        },
    ]
    gtfs_static_file.transfers.return_value = [
        {"from_stop_id": STOP_ID, "to_stop_id": STOP_ID_2},
        {"from_stop_id": STOP_ID, "to_stop_id": STOP_ID},
    ]

    expected_station = parse.Stop(
        id="FakeID", name="", longitude=0, latitude=0, is_station=False
    )
    mock_create_station.return_value = expected_station
    expected_stop_1 = parse.Stop(
        id=STOP_ID,
        name=STOP_NAME,
        longitude=float(STOP_LON),
        latitude=float(STOP_LAT),
        is_station=True,
        parent_stop=expected_station,
    )
    expected_stop_2 = parse.Stop(
        id=STOP_ID_2,
        name=STOP_NAME_2,
        longitude=float(STOP_LON),
        latitude=float(STOP_LAT),
        is_station=True,
        parent_stop=expected_station,
    )

    actual_stops = list(gtfsstaticparser._parse_stops(gtfs_static_file))

    assert [expected_stop_1, expected_stop_2, expected_station] == actual_stops


def test_create_station_from_child_stops():
    child_1 = parse.Stop(
        id="A", name="Name 1", latitude=4, longitude=1, is_station=True
    )
    child_2 = parse.Stop(
        id="B", name="Name 1", latitude=1, longitude=1, is_station=True
    )
    child_3 = parse.Stop(
        id="C", name="Name 2", latitude=1, longitude=1, is_station=True
    )

    expected_station = parse.Stop(
        id="A-B-C", name="Name 1", latitude=2, longitude=1, is_station=True
    )

    actual_station = gtfsstaticparser._create_station_from_child_stops(
        [child_1, child_2, child_3]
    )

    assert expected_station == actual_station


def test_create_station_from_child_stops_hybrid_name():
    child_1 = parse.Stop(
        id="A", name="Name 1", latitude=3, longitude=1, is_station=True
    )
    child_2 = parse.Stop(
        id="B", name="Name 2", latitude=1, longitude=1, is_station=True
    )

    expected_station = parse.Stop(
        id="A-B", name="Name 1 / Name 2", latitude=2, longitude=1, is_station=True
    )

    actual_station = gtfsstaticparser._create_station_from_child_stops(
        [child_1, child_2]
    )

    assert expected_station == actual_station


def test_create_station_from_child_stops_substring_case():
    child_1 = parse.Stop(
        id="A", name="Name 1", latitude=3, longitude=1, is_station=True
    )
    child_2 = parse.Stop(
        id="B", name="Name 1 (and more)", latitude=1, longitude=1, is_station=True
    )

    expected_station = parse.Stop(
        id="A-B", name="Name 1 (and more)", latitude=2, longitude=1, is_station=True
    )

    actual_station = gtfsstaticparser._create_station_from_child_stops(
        [child_1, child_2]
    )

    assert expected_station == actual_station


def test_parse_services():
    gtfs_static_file = mock.Mock()

    gtfs_static_file.stop_times.return_value = [
        {
            "trip_id": TRIP_ID,
            "stop_id": STOP_ID,
            "stop_sequence": "1",
            "departure_time": "11:12:13",
            "arrival_time": "11:12:13",
        },
        {
            "trip_id": "Unknown trip ID",
            "stop_id": STOP_ID_2,
            "stop_sequence": "1",
            "departure_time": "11:12:13",
            "arrival_time": "11:12:13",
        },
    ]
    stop_time = parse.ScheduledTripStopTime(
        stop_sequence=1,
        stop_id=STOP_ID,
        departure_time=datetime.time(hour=11, minute=12, second=13),
        arrival_time=datetime.time(hour=11, minute=12, second=13),
    )

    gtfs_static_file.trips.return_value = [
        {
            "service_id": SERVICE_ID,
            "trip_id": TRIP_ID,
            "route_id": ROUTE_ID,
            "direction_id": "1",
        },
        {
            "service_id": "Unknown service ID",
            "trip_id": TRIP_ID,
            "route_id": ROUTE_ID,
            "direction_id": "1",
        },
    ]
    trip = parse.ScheduledTrip(
        id=TRIP_ID, route_id=ROUTE_ID, direction_id=True, stop_times=[stop_time]
    )

    gtfs_static_file.calendar.return_value = [
        {
            "service_id": SERVICE_ID,
            "monday": "1",
            "tuesday": "1",
            "wednesday": "1",
            "thursday": "0",
            "friday": "0",
            "saturday": "0",
            "sunday": "0",
        }
    ]
    service = parse.ScheduledService(
        id=SERVICE_ID,
        monday=True,
        tuesday=True,
        wednesday=True,
        thursday=False,
        friday=False,
        saturday=False,
        sunday=False,
        trips=[trip],
    )

    actual_services = list(gtfsstaticparser._parse_schedule(gtfs_static_file))

    assert [service] == actual_services


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
            gtfsstaticparser._GtfsStaticFile._InternalFileName.CALENDAR: "calendar",
            gtfsstaticparser._GtfsStaticFile._InternalFileName.ROUTES: "routes",
            gtfsstaticparser._GtfsStaticFile._InternalFileName.STOPS: "stops",
            gtfsstaticparser._GtfsStaticFile._InternalFileName.STOP_TIMES: "stop_times",
            gtfsstaticparser._GtfsStaticFile._InternalFileName.TRANSFERS: "transfers",
            gtfsstaticparser._GtfsStaticFile._InternalFileName.TRIPS: "trips",
        }

        for file_name, func_name in file_name_to_func_name.items():
            binary_content = self._create_zip(file_name.value, csv)
            gtfs_file = gtfsstaticparser._GtfsStaticFile(binary_content)
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
            gtfsstaticparser._GtfsStaticFile._InternalFileName.STOPS.value, csv
        )

        actual = list(gtfsstaticparser._GtfsStaticFile(binary_content).routes())

        self.assertEqual([], actual)

    @staticmethod
    def _create_zip(file_name, file_content):
        buff = io.BytesIO()
        zip_file = zipfile.ZipFile(buff, mode="w")
        zip_file.writestr(file_name, file_content)
        zip_file.close()
        buff.seek(0)
        return buff.read()
