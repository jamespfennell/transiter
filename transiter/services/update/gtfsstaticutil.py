import csv
import os
# Mode: GTFS stations are Transiter stops

from transiter import models
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

# If auto flush is off does this speed things up?
# https://stackoverflow.com/questions/32922210/why-does-a-query-invoke-a-auto-flush-in-sqlalchemy
# class TimetabledService
# class TimetabledTrip
# class TimetabledTripStopTime
# TripStopTime


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
        self.service_id_to_service = {}
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
        #self._parse_trips()
        #self._parse_stop_times()
        #self._parse_transfers()

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
            service = models.ScheduledService()
            service.id = row['service_id']
            for day in days:
                service.__setattr__(day, row[day] == '1')
            self.service_id_to_service[row['service_id']] = service

    def _parse_trips(self):
        for row in self._iterate_over(self.TRIPS_FILE_NAME):
            service_id = row['service_id']
            service = self.service_id_to_service.get(service_id, None)
            if service is None:
                continue
            route = self.route_id_to_route.get(row['route_id'], None)
            if route is None:
                continue
            trip = models.ScheduledTrip()
            trip.id = row['trip_id']
            trip.route = route
            trip.service = service
            trip.direction_id = (row['direction_id'] == '1')
            self.trip_id_to_trip[trip.id] = trip

    def _parse_stop_times(self):
        for row in self._iterate_over(self.STOP_TIMES_FILE_NAME):
            trip_id = row['trip_id']
            trip = self.trip_id_to_trip.get(trip_id, None)
            if trip is None:
                continue
            stop_id = row['stop_id']
            stop = self.stop_id_to_stop.get(stop_id, None)
            if stop is None:
                continue
            trip_stop_time = models.ScheduledTripStopTime()
            trip_stop_time.trip = trip
            trip_stop_time.stop = stop
            trip_stop_time.stop_sequence = row['stop_sequence']

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

import csv
class LightCsvReader:
    class _Row:
        def __init__(self, reader, cells):
            self._reader = reader
            self._cells = cells

        def __getitem__(self, key):
            position = self._reader.column_name_to_position[key]
            return self._cells[position]

    def __init__(self, file_handle):
        self._file_handle = file_handle
        header_row = file_handle.readline().strip().split(',')
        self.column_name_to_position = {
            column_name: position
            for position, column_name
            in enumerate(header_row)
        }

    def __iter__(self):
        return self

    def __next__(self):
        row = self._file_handle.readline()
        if row == '':
            raise StopIteration
        return self._Row(self, row.strip().split(','))


class SqlInsertStatementsBuilder:
    def __init__(self, table_name, columns, num_rows_per_insert):
        self._sql_prefix = 'INSERT INTO {} ({}) VALUES \n'.format(
            table_name, ','.join(columns)
        )
        self._raw_rows = []
        self._raw_rows_cells = []
        self._num_columns = len(columns)
        self._num_rows_per_insert = num_rows_per_insert

    def add_row(self, cells):
        assert len(cells) == self._num_columns
        self._raw_rows_cells.append(cells)
        self._raw_rows.append(','.join(cells))

    def statements(self):
        for i in range(0, len(self._raw_rows), self._num_rows_per_insert):
            rows = self._raw_rows[i:i + self._num_rows_per_insert]
            yield self._sql_prefix + '(' + '),\n('.join(rows) + ');'
    def statements2(self):
        for row in self._raw_rows_cells:
            yield (
                "INSERT INTO scheduled_trip_stop_time (trip_pk, stop_pk"
                ", stop_sequence) VALUES (:trip_pk, :stop_pk, :stop_sequence)",
                {
                    "trip_pk": row[0],
                    'stop_pk': row[1],
                    'stop_sequence': row[2]
                }
            )

    def statements3(self):
        for i in range(0, len(self._raw_rows), self._num_rows_per_insert):
            rows = self._raw_rows_cells[i:i + self._num_rows_per_insert]
            yield (
                #models.ScheduledTripStopTime.__table__.insert(),
                "INSERT INTO scheduled_trip_stop_time (trip_pk, stop_pk"
                ", stop_sequence) VALUES (:trip_pk, :stop_pk, :stop_sequence)",
                [
                    {
                        "trip_pk": row[0],
                        'stop_pk': row[1],
                        'stop_sequence': row[2]
                    }
                    for row in rows
                ]
            )

import time, csv
# https://docs.sqlalchemy.org/en/latest/faq/performance.html
# ^ run to see if we can match that

def fast_scheduled_entities_inserter(
        gtfs_static_zip_data,
        system_pk,
        route_id_to_pk,
        stop_id_to_pk,
):
    """
    This function syncs scheduled entities (services, trips and stop times)
    with the DB by executing a broad SQL DELETE query, and then
    manually constructing and executing three SQL INSERT queries. In a typical
    GTFS static feed there can be hundreds of thousands of scheduled entities;
    by bypassing SQL Alchemy in this specific case, the GTFS static parser can
    be made much more performant. For the NYC Subway GTFS static data, this
    function reduces this step from about 3 minutes to about 20 seconds.

    This is only really possible because other
    Transiter entities do not rely on scheduled entities, so performing a full
    DELETE followed by INSERT does not corrupt any foreign key references.

    :param gtfs_static_zip_data:
    :param system_pk:
    :param route_id_to_pk:
    :param stop_id_to_pk:
    :param stop_id_to_station_pk
    :return:
    """
    # TODO: when the gtfsstatic becomes a feed, first erase all static entities

    zipfile = ZipFile(BytesIO(gtfs_static_zip_data))
    all_file_names = zipfile.namelist()

    from transiter.data import fastoperations
    from transiter.data.dams import genericqueries

    str_to_bool = {
        '0': False,
        '1': True
    }
    with zipfile.open(GtfsStaticParser.CALENDAR_FILE_NAME) as raw_csv_file:
        csv_file = io.TextIOWrapper(raw_csv_file, 'utf-8')
        fast_inserter = fastoperations.FastInserter(models.ScheduledService)
        rows = csv.DictReader(csv_file)
        for row in rows:
            fast_inserter.add(
                {
                    'id': row['service_id'],
                    'system_pk': system_pk,
                    'monday': row['monday'] == '1',
                    'tuesday': str_to_bool[row['tuesday']],
                    'wednesday': str_to_bool[row['wednesday']],
                    'thursday': str_to_bool[row['thursday']],
                    'friday': str_to_bool[row['friday']],
                    'saturday': str_to_bool[row['saturday']],
                    'sunday': str_to_bool[row['sunday']]
                }
            )
        fast_inserter.flush()
        service_id_to_pk = genericqueries.get_id_to_pk_map(
            models.ScheduledService
        )

    trip_id_to_raw_service_map_list = {}
    with zipfile.open(GtfsStaticParser.STOP_TIMES_FILE_NAME) as raw_csv_file:
        csv_file = io.TextIOWrapper(raw_csv_file, 'utf-8')
        rows = csv.DictReader(csv_file)
        for row in rows:
            if row['trip_id'] not in trip_id_to_raw_service_map_list:
                trip_id_to_raw_service_map_list[row['trip_id']] = []
            trip_id_to_raw_service_map_list[row['trip_id']].append(
                stop_id_to_pk[row['stop_id']]
            )

    with zipfile.open(GtfsStaticParser.TRIPS_FILE_NAME) as raw_csv_file:
        csv_file = io.TextIOWrapper(raw_csv_file, 'utf-8')
        fast_inserter = fastoperations.FastInserter(models.ScheduledTrip)
        rows = csv.DictReader(csv_file)
        for row in rows:
            direction_id = str_to_bool[row['direction_id']]
            raw_service_map_str = str(
                trip_id_to_raw_service_map_list[row['trip_id']])
            fast_inserter.add(
                {
                    'id': row['trip_id'],
                    'service_pk': service_id_to_pk[row['service_id']],
                    'route_pk': route_id_to_pk[row['route_id']],
                    'direction_id': direction_id,
                    'raw_service_map_string': raw_service_map_str
                }
            )
        fast_inserter.flush()
        trip_id_to_pk = genericqueries.get_id_to_pk_map(
            models.ScheduledTrip
        )
    import datetime

    def time_str_to_datetime_time(time_str):
        hour, minute, second = time_str.split(':')
        return datetime.time(
            hour=int(hour) % 24,
            minute=int(minute),
            second=int(second)
        )

    with zipfile.open(GtfsStaticParser.STOP_TIMES_FILE_NAME) as raw_csv_file:
        csv_file = io.TextIOWrapper(raw_csv_file, 'utf-8')
        fast_inserter = fastoperations.FastInserter(
            models.ScheduledTripStopTime)
        rows = csv.DictReader(csv_file)

        for row in rows:
            fast_inserter.add(
                {
                    'trip_pk': trip_id_to_pk[row['trip_id']],
                    'stop_pk': stop_id_to_pk[row['stop_id']],
                    'stop_sequence': row['stop_sequence'],
                    'departure_time': time_str_to_datetime_time(row['departure_time']),
                    'arrival_time': time_str_to_datetime_time(row['arrival_time']),
                }
            )
        fast_inserter.flush()
