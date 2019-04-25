import os
from io import BytesIO
from zipfile import ZipFile

from transiter import models
from transiter.data import database
from transiter.data.dams import routedam, stopdam
from transiter.models import Route, Stop

# Mode: GTFS stations are Transiter stops
days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday',
        'sunday']
def parse_gtfs_static(feed, gtfs_static_zip_data):
    system = feed.system

    gtfs_static_parser = GtfsStaticParser()
    gtfs_static_parser.parse_from_zip_data(gtfs_static_zip_data)

    for route in gtfs_static_parser.route_id_to_route.values():
        route.system = system

    stop_id_to_station_id = {}

    # next 3 bits: Construct larger stations using transfers.txt
    # TODO: make a separate method in the GTFS parser or stopgraphmanager.py
    station_sets_by_stop_id = {}
    for stop in gtfs_static_parser.stop_id_to_stop.values():
        stop.system = system
        if not stop.is_station:
            parent_stop = gtfs_static_parser.stop_id_to_stop.get(stop.parent_stop_id, None)
            if parent_stop is None:
                stop.is_station = True
            else:
                stop.parent_stop = parent_stop
        if stop.is_station:
            station_sets_by_stop_id[stop.id] = {stop.id}
        else:
            stop_id_to_station_id[stop.id] = stop.parent_stop.id

    for (stop_id_1, stop_id_2) in gtfs_static_parser.transfer_tuples:
        print(stop_id_1, stop_id_2)
        updated_station_set = station_sets_by_stop_id[stop_id_1].union(
            station_sets_by_stop_id[stop_id_2])
        for stop_id in updated_station_set:
            station_sets_by_stop_id[stop_id] = updated_station_set

    for station_set in station_sets_by_stop_id.values():
        if len(station_set) <= 1:
            continue
        parent_stop = models.Stop()
        child_stops = [gtfs_static_parser.stop_id_to_stop[stop_id] for stop_id in station_set]
        for child_stop in child_stops:
            child_stop.parent_stop = parent_stop
        _lift_stop_properties(parent_stop, child_stops)
        parent_stop.is_station = True
        parent_stop.system = system

        station_set.clear()
    session = database.get_session()
    session.flush()

    route_id_to_pk = routedam.get_id_to_pk_map_in_system(system.id)
    stop_id_to_pk = stopdam.get_id_to_pk_map_in_system(system.id)

    fast_scheduled_entities_inserter(
        gtfs_static_zip_data,
        system.pk,
        route_id_to_pk,
        stop_id_to_pk,
    )
    session.flush()
    from transiter.services.servicepattern import servicepatternmanager
    servicepatternmanager.calculate_scheduled_service_maps_for_system(system)

    # for service in gtfs_static_parser.service_id_to_service.values():
    #    service.system = system


# TODO: move to gtfs static
def _lift_stop_properties(parent_stop, child_stops):
    parent_stop.latitude = sum(float(child_stop.latitude) for child_stop in child_stops) / len(child_stops)
    parent_stop.longitude = sum(float(child_stop.longitude) for child_stop in child_stops) / len(child_stops)

    if parent_stop.id is None:
        child_stop_ids = [child_stop.id for child_stop in child_stops]
        parent_stop.id = '-'.join(sorted(child_stop_ids))

    if parent_stop.name is None:
        child_stop_names = {child_stop.name: 0 for child_stop in child_stops}
        for child_stop in child_stops:
            child_stop_names[child_stop.name] += 1
        max_freq = max(child_stop_names.values())
        most_frequent_names = set()
        for child_stop_name, freq in child_stop_names.items():
            if freq == max_freq:
                most_frequent_names.add(child_stop_name)

        for name in most_frequent_names.copy():
            remove = False
            for other_name in most_frequent_names:
                if name != other_name and name in other_name:
                    remove = True
            if remove:
                most_frequent_names.remove(name)
        parent_stop.name = ' / '.join(sorted(most_frequent_names))










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
            print(all_file_names)
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
            # TODO: the spirit was right, the implementation wrong
            if row['location_type'] == '1':
                continue
            stop.is_station = False
            stop.parent_stop_id = row.get('parent_station', None)
            self.stop_id_to_stop[stop.id] = stop

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

import csv
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

    with zipfile.open(GtfsStaticParser.TRIPS_FILE_NAME) as raw_csv_file:
        csv_file = io.TextIOWrapper(raw_csv_file, 'utf-8')
        fast_inserter = fastoperations.FastInserter(models.ScheduledTrip)
        rows = csv.DictReader(csv_file)
        for row in rows:
            direction_id = str_to_bool[row['direction_id']]
            fast_inserter.add(
                {
                    'id': row['trip_id'],
                    'service_pk': service_id_to_pk[row['service_id']],
                    'route_pk': route_id_to_pk[row['route_id']],
                    'direction_id': direction_id,
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
