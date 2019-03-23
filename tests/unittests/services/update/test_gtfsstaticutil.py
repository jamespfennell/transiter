import unittest
from unittest import mock
from transiter.services.update import gtfsstaticutil
from transiter import models


class TestGtfsStaticUtil(unittest.TestCase):

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
        route.id = '1'
        route.color = '2'
        route.timetable_url = '3'
        route.short_name = '4'
        route.long_name = '5'
        route.description = '6'

        def csv_iterator(file_path):
            yield data

        gtfs_static_parser = gtfsstaticutil.GtfsStaticParser()
        gtfs_static_parser._base_path = ''
        gtfs_static_parser._iterate_over = csv_iterator

        gtfs_static_parser._parse_routes()

        self.assertEqual(
            gtfs_static_parser.route_id_to_route,
            {'1': route}
        )

    def test_parse_stops(self):
        """[GTFS static util] Parse stops, full stop case"""

        data = {
            'stop_id': '1',
            'stop_name': '2',
            'stop_lon': '3',
            'stop_lat': '4',
            'parent_station': '5',
            'location_type': '1',
        }
        stop = models.Stop()
        stop.id = '1'
        stop.name = '2'
        stop.longitude = '3'
        stop.latitude = '4'
        stop.is_station = True

        def csv_iterator(file_path):
            yield data

        gtfs_static_parser = gtfsstaticutil.GtfsStaticParser()
        gtfs_static_parser._base_path = ''
        gtfs_static_parser._iterate_over = csv_iterator

        gtfs_static_parser._parse_stops()

        self.assertEqual(
            gtfs_static_parser.stop_id_to_stop,
            {'1': stop}
        )

    @mock.patch('transiter.services.update.gtfsstaticutil.os')
    def test_parse_transfers(self, os):
        """[GTFS static util] Parse transfers"""
        os.path.exists.return_value = True
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
        gtfs_static_parser._iterate_over = csv_iterator

        gtfs_static_parser._parse_transfers()

        self.assertEqual(
            gtfs_static_parser.transfer_tuples,
            [(stop_id_1, stop_id_2)]
        )

    def test_parse_transfers_same_stop(self):
        """[GTFS static util] Parse transfers same stop case"""
        stop_id_1 = 'service!'
        data = {
            'from_stop_id': stop_id_1,
            'to_stop_id': stop_id_1
        }

        def csv_iterator(file_path):
            yield data

        gtfs_static_parser = gtfsstaticutil.GtfsStaticParser()
        gtfs_static_parser._base_path = ''
        gtfs_static_parser._iterate_over = csv_iterator

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

