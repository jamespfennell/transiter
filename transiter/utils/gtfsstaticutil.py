import csv
import os
# Mode: GTFS stations are Transiter stops

from transiter.database.models import Route, Stop, StopAlias

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
        self._stop_id_alias_to_stop_id = {}
        self.stop_id_alias_to_stop_alias = {}
        self._service_id_to_service = {}
        self.trip_id_to_trip = {}
        self._base_path = None
        self.transfer_tuples = []

    def parse_from_directory(self, path):
        self._base_path = path
        self._parse_routes()
        self._parse_stops()
        self._parse_services()
        self._parse_trips()
        self._parse_stop_times()
        self._parse_transfers()

    def _parse_routes(self):
        routes_file_path = os.path.join(
            self._base_path, self.ROUTES_FILE_NAME)
        for row in self._csv_iterator(routes_file_path):
            route = Route()
            route.route_id = row['route_id']
            route.color = row['route_color']
            route.timetable_url = row['route_url']
            route.short_name = row['route_short_name']
            route.long_name = row['route_long_name']
            route.description = row['route_desc']
            self.route_id_to_route[route.route_id] = route

    def _parse_stops(self):
        stops_file_path = os.path.join(
            self._base_path, self.STOPS_FILE_NAME)
        for row in self._csv_iterator(stops_file_path):
            if row['location_type'] == '0':
                stop_alias = StopAlias()
                stop_alias.stop_id = row['parent_station']
                stop_alias.stop_id_alias = row['stop_id']
                # TODO: get rid of this
                self._stop_id_alias_to_stop_id[
                    stop_alias.stop_id_alias] = stop_alias.stop_id
                self.stop_id_alias_to_stop_alias[
                    stop_alias.stop_id_alias] = stop_alias
                continue
            stop = Stop()
            stop.stop_id = row['stop_id']
            stop.name = row['stop_name']
            stop.longitude = row['stop_lon']
            stop.latitude = row['stop_lat']
            self.stop_id_to_stop[stop.stop_id] = stop

    def _parse_services(self):
        calendar_file_path = os.path.join(
            self._base_path, self.CALENDAR_FILE_NAME)
        for row in self._csv_iterator(calendar_file_path):
            service = _GtfsStaticService()
            for day in days:
                service.__setattr__(day, row[day] == '1')
            self._service_id_to_service[row['service_id']] = service

    def _parse_trips(self):
        trip_file_path = os.path.join(
            self._base_path, self.TRIPS_FILE_NAME)
        for row in self._csv_iterator(trip_file_path):
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
        stop_times_file_path = os.path.join(
            self._base_path, self.STOP_TIMES_FILE_NAME)
        for row in self._csv_iterator(stop_times_file_path):
            trip_id = row['trip_id']
            trip = self.trip_id_to_trip.get(trip_id, None)
            if trip is None:
                continue

            # TODO: remove assumption that stop sequence is increasing
            pre_stop_id = row['stop_id']
            if pre_stop_id in self.stop_id_to_stop:
                stop_id = pre_stop_id
            elif pre_stop_id in self._stop_id_alias_to_stop_id:
                stop_id = self._stop_id_alias_to_stop_id[pre_stop_id]
            else:
                continue

            if trip.start_time is None:
                trip.start_time = self._transform_times(row['departure_time'])
                trip.end_time = trip.start_time
            else:
                trip.end_time = self._transform_times(row['arrival_time'])
            trip.stop_ids.append(stop_id)

    def _parse_transfers(self):
        transfers_file_path = os.path.join(
            self._base_path, self.TRANSFERS_FILE_NAME)
        for row in self._csv_iterator(transfers_file_path):
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

    @staticmethod
    def _csv_iterator(csv_file_path):
        with open(csv_file_path) as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                yield row

