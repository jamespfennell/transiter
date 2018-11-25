import unittest
from unittest import mock
from transiter.utils import gtfsstaticutil
from transiter import models


class TestGtfsStaticUtil(unittest.TestCase):

    def test_gtfs_static_service_not_equal(self):
        service_one = gtfsstaticutil._GtfsStaticService()
        service_one.monday = True
        service_two = gtfsstaticutil._GtfsStaticService()
        service_two.monday = False
        self.assertNotEqual(service_one, service_two)

    def test_static_trip_not_equal(self):
        service_one = gtfsstaticutil.StaticTrip()
        service_one.monday = True
        service_two = gtfsstaticutil.StaticTrip()
        service_two.monday = False
        self.assertNotEqual(service_one, service_two)

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
        gtfs_static_parser._csv_iterator = csv_iterator

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
        gtfs_static_parser._csv_iterator = csv_iterator

        gtfs_static_parser._parse_stops()

        self.assertEqual(
            gtfs_static_parser.stop_id_to_stop,
            {'1': stop}
        )
        self.assertEqual(gtfs_static_parser.stop_id_alias_to_stop_alias, {})
        self.assertEqual(gtfs_static_parser._stop_id_alias_to_stop_id, {})

    def test_parse_services(self):
        """[GTFS static util] Parse services"""
        service_id = 'service!'
        # TODO extract all constants in this class out
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

    def test_parse_trips_no_service(self):
        """[GTFS static util] Parse trips, no service case"""
        data = {
            'service_id': '1'
        }

        def csv_iterator(file_path):
            yield data

        gtfs_static_parser = gtfsstaticutil.GtfsStaticParser()
        gtfs_static_parser._base_path = ''
        gtfs_static_parser._csv_iterator = csv_iterator

        gtfs_static_parser._parse_trips()

        self.assertEqual(gtfs_static_parser.trip_id_to_trip, {})

    def test_parse_trips(self):
        """[GTFS static util] Parse trips"""
        data = {
            'service_id': '1',
            'route_id': '2',
            'trip_id': '7',
            'direction_id': '0'
        }
        service = gtfsstaticutil._GtfsStaticService()
        service.monday = '2'
        service.tuesday = '3'
        trip = gtfsstaticutil.StaticTrip()
        trip.route_id = '2'
        trip.monday = '2'
        trip.tuesday = '3'
        trip.direction_id = True

        def csv_iterator(file_path):
            yield data

        gtfs_static_parser = gtfsstaticutil.GtfsStaticParser()
        gtfs_static_parser._base_path = ''
        gtfs_static_parser._csv_iterator = csv_iterator
        gtfs_static_parser._service_id_to_service = {
            '1': service
        }

        gtfs_static_parser._parse_trips()

        self.assertEqual(
            gtfs_static_parser.trip_id_to_trip,
            {'7': trip})

    def test_parse_stop_times_unknown_trip(self):
        """[GTFS static util] Parse stop time, unknown trip case"""
        data = {
            'trip_id': '1',
        }

        def csv_iterator(file_path):
            yield data

        gtfs_static_parser = gtfsstaticutil.GtfsStaticParser()
        gtfs_static_parser._base_path = ''
        gtfs_static_parser._csv_iterator = csv_iterator
        gtfs_static_parser._transform_times = mock.MagicMock()

        gtfs_static_parser._parse_stop_times()

        gtfs_static_parser._transform_times.assert_not_called()

    def test_parse_stop_times_unknown_stop(self):
        """[GTFS static util] Parse stop time, unknown stop case"""
        data = {
            'trip_id': '1',
            'stop_id': '2'
        }
        trip = gtfsstaticutil.StaticTrip()
        post_trip = gtfsstaticutil.StaticTrip()

        def csv_iterator(file_path):
            yield data

        gtfs_static_parser = gtfsstaticutil.GtfsStaticParser()
        gtfs_static_parser._base_path = ''
        gtfs_static_parser._csv_iterator = csv_iterator
        gtfs_static_parser.trip_id_to_trip = {'1': trip}
        gtfs_static_parser._transform_times = mock.MagicMock()

        gtfs_static_parser._parse_stop_times()

        self.assertEqual(trip, post_trip)
        gtfs_static_parser._transform_times.assert_not_called()

    def test_parse_stop_times_no_start_time(self):
        """[GTFS static util] Parse stop time, no trip start time and regular stop"""
        data = {
            'trip_id': '1',
            'stop_id': '2',
            'departure_time': '3'
        }
        trip = gtfsstaticutil.StaticTrip()
        post_trip = gtfsstaticutil.StaticTrip()
        post_trip.start_time = '14'
        post_trip.end_time = '14'
        post_trip.stop_ids = ['2']

        def csv_iterator(file_path):
            yield data

        gtfs_static_parser = gtfsstaticutil.GtfsStaticParser()
        gtfs_static_parser._base_path = ''
        gtfs_static_parser._csv_iterator = csv_iterator
        gtfs_static_parser.trip_id_to_trip = {'1': trip}
        gtfs_static_parser.stop_id_to_stop = {'2': None}
        gtfs_static_parser._transform_times = mock.MagicMock()
        gtfs_static_parser._transform_times.return_value = '14'

        gtfs_static_parser._parse_stop_times()

        self.assertEqual(trip, post_trip)
        gtfs_static_parser._transform_times.assert_called_once_with('3')

    def test_parse_stop_times_alias(self):
        """[GTFS static util] Parse stop time, with stop id alias"""
        data = {
            'trip_id': '1',
            'stop_id': '2',
            'departure_time': '3',
            'arrival_time': '4',
        }
        trip = gtfsstaticutil.StaticTrip()
        trip.start_time = '13'
        post_trip = gtfsstaticutil.StaticTrip()
        post_trip.start_time = '13'
        post_trip.end_time = '14'
        post_trip.stop_ids = ['7']

        def csv_iterator(file_path):
            yield data

        gtfs_static_parser = gtfsstaticutil.GtfsStaticParser()
        gtfs_static_parser._base_path = ''
        gtfs_static_parser._csv_iterator = csv_iterator
        gtfs_static_parser.trip_id_to_trip = {'1': trip}
        gtfs_static_parser._stop_id_alias_to_stop_id = {'2': '7'}
        gtfs_static_parser._transform_times = mock.MagicMock()
        gtfs_static_parser._transform_times.return_value = '14'

        gtfs_static_parser._parse_stop_times()

        self.assertEqual(trip, post_trip)
        gtfs_static_parser._transform_times.assert_called_once_with('4')

    @mock.patch('transiter.utils.gtfsstaticutil.os')
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
        gtfs_static_parser._csv_iterator = csv_iterator

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
