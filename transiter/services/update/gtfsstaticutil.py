import csv
import os
# Mode: GTFS stations are Transiter stops

from transiter.models import Route, Stop

from io import BytesIO
from zipfile import ZipFile
days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday',
        'sunday']


class _GtfsStaticService:
    def __init__(self):
        for day in days:
            self.__setattr__(day, None)

    def __eq__(self, other):
        for day in days:
            if getattr(self, day) != getattr(other, day):
                return False
        return True


class StaticTrip:

    def __init__(self):
        self.route_id = None
        self.direction_id = None
        for day in days:
            self.__setattr__(day, None)
        self.stop_ids = []
        self.start_time = None
        self.end_time = None

    def reverse(self):
        self.direction_id = not self.direction_id
        self.stop_ids.reverse()

    def __hash__(self):
        return hash((
            self.route_id,
            self.direction_id,
            self.start_time,
            self.end_time,
            tuple(self.stop_ids)
        ))

    def __eq__(self, other):
        for day in days:
            if getattr(self, day) != getattr(other, day):
                return False
        return (
            self.route_id == other.route_id and
            self.direction_id == other.direction_id and
            self.start_time == other.start_time and
            self.end_time == other.end_time and
            self.stop_ids == other.stop_ids
        )

import io
class GtfsStaticParser:

    CALENDAR_FILE_NAME = 'calendar.txt'
    ROUTES_FILE_NAME = 'routes.txt'
    STOP_TIMES_FILE_NAME = 'stop_times.txt'
    STOPS_FILE_NAME = 'stops.txt'
    TRANSFERS_FILE_NAME = 'transfers.txt'
    TRIPS_FILE_NAME = 'trips.txt'

    def __init__(self):
        self.route_id_to_route = {}
        self.stop_id_to_stop = {}
        self._service_id_to_service = {}
        self.trip_id_to_trip = {}
        self.transfer_tuples = []

    def _iterate_over(self, file_name):
        raise NotImplementedError

    @staticmethod
    def _iterate_over_zip_builder(zipfile):
        all_file_names = zipfile.namelist()

        def _iterate_over(file_name):
            if file_name not in all_file_names:
                return []
            with zipfile.open(file_name) as raw_csv_file:
                csv_file = io.TextIOWrapper(raw_csv_file, 'utf-8')
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    yield row
                    
        return _iterate_over

    @staticmethod
    def _iterate_over_directory_builder(base_path):
        def _iterate_over(file_name):
            # TODO: for optional files, check for existence
            file_path = os.path.join(base_path, file_name)
            with open(file_path) as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    yield row
        return _iterate_over

    def parse_from_zip_data(self, zip_data):
        zipfile = ZipFile(BytesIO(zip_data))
        self._iterate_over = self._iterate_over_zip_builder(zipfile)
        self._parse()

    def parse_from_directory(self, path):
        self._iterate_over = self._iterate_over_directory_builder(path)
        self._parse()

    def _parse(self):
        self._parse_routes()
        self._parse_stops()
        self._parse_services()
        self._parse_trips()
        self._parse_stop_times()
        self._parse_transfers()

    def _parse_routes(self):
        for row in self._iterate_over(self.ROUTES_FILE_NAME):
            route = Route()
            route.id = row['route_id']
            route.color = row.get('route_color')
            route.timetable_url = row.get('route_url')
            route.short_name = row.get('route_short_name')
            route.long_name = row.get('route_long_name')
            route.description = row.get('route_desc')
            self.route_id_to_route[route.id] = route

    def _parse_stops(self):
        for row in self._iterate_over(self.STOPS_FILE_NAME):
            stop = Stop()
            stop.id = row['stop_id']
            stop.name = row['stop_name']
            stop.longitude = row['stop_lon']
            stop.latitude = row['stop_lat']

            if row['location_type'] == '1':
                stop.is_station = True
                stop.parent_stop_id = None
                self.stop_id_to_stop[stop.id] = stop
            if row['location_type'] != '0':
                continue
            stop.is_station = False
            stop.parent_stop_id = row.get('parent_station', None)
            self.stop_id_to_stop[stop.id] = stop

    def _parse_services(self):
        for row in self._iterate_over(self.CALENDAR_FILE_NAME):
            service = _GtfsStaticService()
            for day in days:
                service.__setattr__(day, row[day] == '1')
            self._service_id_to_service[row['service_id']] = service

    def _parse_trips(self):
        for row in self._iterate_over(self.TRIPS_FILE_NAME):
            service_id = row['service_id']
            service = self._service_id_to_service.get(service_id, None)
            if service is None:
                continue
            trip = StaticTrip()
            trip.route_id = row['route_id']
            trip.direction_id = (row['direction_id'] == '0')
            for day in days:
                trip.__setattr__(day, getattr(service, day))
            self.trip_id_to_trip[row['trip_id']] = trip

    def _parse_stop_times(self):
        for row in self._iterate_over(self.STOP_TIMES_FILE_NAME):
            trip_id = row['trip_id']
            trip = self.trip_id_to_trip.get(trip_id, None)
            if trip is None:
                continue

            # TODO: remove assumption that stop sequence is increasing
            pre_stop_id = row['stop_id']
            if pre_stop_id in self.stop_id_to_stop:
                stop_id = pre_stop_id
            else:
                print('Test')
                continue

            if trip.start_time is None:
                trip.start_time = self._transform_times(row['departure_time'])
                trip.end_time = trip.start_time
            else:
                trip.end_time = self._transform_times(row['arrival_time'])
            trip.stop_ids.append(stop_id)

    def _parse_transfers(self):
        for row in self._iterate_over(self.TRANSFERS_FILE_NAME):
            stop_id_1 = row['from_stop_id']
            stop_id_2 = row['to_stop_id']
            if stop_id_1 == stop_id_2:
                continue
            self.transfer_tuples.append((stop_id_1, stop_id_2))

    @staticmethod
    def _transform_times(gtfs_static_time):
        hours = int(gtfs_static_time[0:2])
        mins = int(gtfs_static_time[3:5])
        secs = int(gtfs_static_time[6:8])
        return hours + mins/60 + secs/3600


