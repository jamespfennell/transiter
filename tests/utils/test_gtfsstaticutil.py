import unittest
from unittest import mock
from transiter.utils import gtfsstaticutil
from transiter.database import models


class TestGtfsStaticUtil(unittest.TestCase):

    def test_parse_from_directory(self):
        """[GTFS static util] Parse from directory"""

        directory = 'Dir'

        gtfs_static_parser = gtfsstaticutil.GtfsStaticParser()
        gtfs_static_parser._parse_routes = mock.MagicMock()
        gtfs_static_parser._parse_stops = mock.MagicMock()
        gtfs_static_parser._parse_services = mock.MagicMock()
        gtfs_static_parser._parse_trips = mock.MagicMock()
        gtfs_static_parser._parse_stop_times = mock.MagicMock()
        gtfs_static_parser._parse_transfers = mock.MagicMock()

        gtfs_static_parser.parse_from_directory(directory)

        self.assertEqual(gtfs_static_parser._base_path, directory)

        gtfs_static_parser._parse_routes.assert_called_once_with()
        gtfs_static_parser._parse_stops.assert_called_once_with()
        gtfs_static_parser._parse_services.assert_called_once_with()
        gtfs_static_parser._parse_trips.assert_called_once_with()
        gtfs_static_parser._parse_stop_times.assert_called_once_with()
        gtfs_static_parser._parse_transfers.assert_called_once_with()

    def test_parse_routes(self):
        """[GTFS static util] Parse routes"""

        data = {
            'route_id': '1',
            'route_color': '2',
            'route_url': '3',
            'route_short_name': '4',
            'route_long_name': '5',
            'route_desc': '6'
        }
        route = models.Route()
        route.route_id = '1'
        route.color = '2'
        route.timetable_url = '3'
        route.short_name = '4'
        route.long_name = '5'
        route.description = '6'

        def csv_iterator(file_path):
            yield data

        gtfs_static_parser = gtfsstaticutil.GtfsStaticParser()
        gtfs_static_parser._base_path = ''
        gtfs_static_parser._csv_iterator = csv_iterator

        gtfs_static_parser._parse_routes()

        self.assertEqual(
            gtfs_static_parser.route_id_to_route,
            {'1': route}
        )

    def test_parse_services(self):
        """[GTFS static util] Parse services"""
        service_id = 'service!'
        data = {
            'service_id': service_id,
            'monday': '1',
            'tuesday': '0',
            'wednesday': '0',
            'thursday': '1',
            'friday': '0',
            'saturday': '0',
            'sunday': '1'
        }
        service = gtfsstaticutil._GtfsStaticService()
        service.monday = True
        service.tuesday = False
        service.wednesday = False
        service.thursday = True
        service.friday = False
        service.saturday = False
        service.sunday = True

        def csv_iterator(file_path):
            yield data

        gtfs_static_parser = gtfsstaticutil.GtfsStaticParser()
        gtfs_static_parser._base_path = ''
        gtfs_static_parser._csv_iterator = csv_iterator

        gtfs_static_parser._parse_services()

        self.assertEqual(
            gtfs_static_parser._service_id_to_service,
            {service_id: service}
        )

    def test_parse_transfers(self):
        """[GTFS static util] Parse transfers"""
        stop_id_1 = 'service!'
        stop_id_2 = 'MySecond'
        data = {
            'from_stop_id': stop_id_1,
            'to_stop_id': stop_id_2
        }

        def csv_iterator(file_path):
            yield data

        gtfs_static_parser = gtfsstaticutil.GtfsStaticParser()
        gtfs_static_parser._base_path = ''
        gtfs_static_parser._csv_iterator = csv_iterator

        gtfs_static_parser._parse_transfers()

        self.assertEqual(
            gtfs_static_parser.transfer_tuples,
            [(stop_id_1, stop_id_2)]
        )

    def test_parse_transfers_same_stop(self):
        """[GTFS static util] Parse transfers"""
        stop_id_1 = 'service!'
        data = {
            'from_stop_id': stop_id_1,
            'to_stop_id': stop_id_1
        }

        def csv_iterator(file_path):
            yield data

        gtfs_static_parser = gtfsstaticutil.GtfsStaticParser()
        gtfs_static_parser._base_path = ''
        gtfs_static_parser._csv_iterator = csv_iterator

        gtfs_static_parser._parse_transfers()

        self.assertEqual(
            gtfs_static_parser.transfer_tuples,
            []
        )


    def test_transform_times(self):
        """[GTFS static util] Transform GTFS static formatted times"""

        input = '01:12:00'
        expected = 1.2

        actual = gtfsstaticutil.GtfsStaticParser._transform_times(input)

        self.assertEqual(actual, expected)

    @mock.patch('transiter.utils.gtfsstaticutil.open')
    def test_csv_iterator(self, open_func):
        """[GTFS static util] CSV iterator"""

        class ContextManager(object):
            def __init__(self, dummy_resource=None):
                self.dummy_resource = dummy_resource

            def __enter__(self):
                return self.dummy_resource

            def __exit__(self, *args):
                pass
        context_manager = ContextManager([
            'A,B',
            'C,D'
        ])
        open_func.return_value = context_manager
        file_path = 'file_path'
        expected = [{'A': 'C', 'B': 'D'}]

        actual = list(gtfsstaticutil.GtfsStaticParser._csv_iterator(file_path))

        self.assertListEqual(actual, expected)
