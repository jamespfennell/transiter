from ..data import dbconnection
from ..data import dbaccessobjects
from ..data import dbschema
from . import exceptions
from ..utils import routelistutil
import csv
import os
from ..utils import jsonutil

system_dao = dbaccessobjects.SystemDao()


@dbconnection.unit_of_work
def list_all():
    return [_convert(system) for system in system_dao.list()]


@dbconnection.unit_of_work
def get_by_id(system_id):
    system = system_dao.get_by_id(system_id)
    if system is None:
        raise exceptions.IdNotFoundError
    return _convert(system)


@dbconnection.unit_of_work
def install(system_id):
    if system_dao.get_by_id(system_id) is not None:
        return False

    system = system_dao.create()
    system.system_id = system_id

    _import_static_data(system)
    return True

@dbconnection.unit_of_work
def delete(system_id):
    deleted = system_dao.delete(system_id)
    if not deleted:
        raise exceptions.IdNotFoundError
    return True


def _convert(system):
    return {
        'system_id': system.system_id
        #'name': system.name,
        #'routes': routes_data
        }


def _import_static_data(system):
    system_base_dir = os.path.join(
        os.path.dirname(__file__),
        '../systems',
        system.system_id
        )
    agency_data_dir = os.path.join(system_base_dir, 'agencydata')
    custom_data_dir = os.path.join(system_base_dir, 'customdata')
    print(agency_data_dir)

    session = dbconnection.get_session()

    routes_data_file = os.path.join(agency_data_dir, 'routes.txt')
    routes_by_route_id = {}
    with open(routes_data_file, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            route = dbschema.Route()
            session.add(route)
            route.route_id=row['route_id']
            route.color = row['route_color']
            route.timetable_url = row['route_url']
            route.short_name = row['route_short_name']
            route.long_name = row['route_long_name']
            route.description = row['route_desc']
            route.system = system

            routes_by_route_id[route.route_id] = route

    stops_data_file = os.path.join(agency_data_dir, 'stops.txt')
    station_sets_by_stop_id = {}
    stops_by_stop_id = {}
    with open(stops_data_file, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            # Note, this may be NYC subway specific logic: if so extract the
            # it to the NYC subway module
            stop_id = row['stop_id']
            if stop_id[-1] == 'N' or stop_id[-1] == 'S':
                continue

            stop = dbschema.Stop()
            session.add(stop)
            stop.stop_id=row['stop_id']
            stop.name = row['stop_name']
            stop.longitude = row['stop_lon']
            stop.lattitude = row['stop_lat']

            station_sets_by_stop_id[stop_id] = set([stop_id])
            stops_by_stop_id[stop_id] = stop

    transfers_data_file = os.path.join(agency_data_dir, 'transfers.txt')
    with open(transfers_data_file, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            stop_id_1 = row['from_stop_id']
            stop_id_2 = row['to_stop_id']
            if stop_id_1 == stop_id_2:
                continue

            updated_station_set = station_sets_by_stop_id[stop_id_1].union(
                station_sets_by_stop_id[stop_id_2])
            for stop_id in updated_station_set:
                station_sets_by_stop_id[stop_id] = updated_station_set

        for station_set in station_sets_by_stop_id.values():
            if len(station_set) == 0:
                continue

            station = dbschema.Station()
            session.add(station)
            for stop_id in station_set:
                stops_by_stop_id[stop_id].station = station
            station.system = system
            station_set.clear()

    stop_times_data_file = os.path.join(agency_data_dir, 'stop_times.txt')
    route_lists = routelistutil.construct_route_lists_from_stop_times_file(
        system,
        stop_times_data_file
    )
    for (route_id, route_list) in route_lists.items():
        route = routes_by_route_id[route_id]
        position = 0
        for stop_id in route_list:
            route_list_entry = dbschema.RouteListEntry()
            session.add(route_list_entry)
            route_list_entry.route = route
            route_list_entry.stop = stops_by_stop_id[stop_id]
            route_list_entry.position = position
            position += 1

    # The following two data imports are definitely custom logic, though
    # custom to the program rather than the NYC subway
    # Default other option: N=north, S=south ;)
    # Also direction name exceptions is a bad name
    sorted_stop_ids = sorted(stops_by_stop_id.keys())
    index = 0
    direction_names_data_file = os.path.join(
        custom_data_dir,
        'direction_names.csv'
        )
    with open(direction_names_data_file, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            while sorted_stop_ids[index] != row['stop_id']:
                north = dbschema.DirectionName()
                session.add(north)
                north.name = row['north_direction_name']
                north.track = None
                north.direction = 'N'
                north.stop = stops_by_stop_id[sorted_stop_ids[index]]

                south = dbschema.DirectionName()
                session.add(south)
                south.name = row['south_direction_name']
                south.track = None
                south.direction = 'S'
                south.stop = stops_by_stop_id[sorted_stop_ids[index]]

                index += 1

    direction_name_exceptions_data_file = os.path.join(
        custom_data_dir,
        'direction_name_exceptions.csv'
        )
    with open(direction_name_exceptions_data_file, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            direction = dbschema.DirectionName()
            session.add(direction)
            direction.name = row['name']
            direction.track = row['track']
            direction.direction = row['direction']
            direction.stop = stops_by_stop_id[row['stop_id']]

    feeds_data_file = os.path.join(custom_data_dir, 'feeds.csv')
    with open(feeds_data_file, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            feed = dbschema.Feed()
            session.add(feed)
            feed.system = system
            feed.feed_id = row['feed_id']
            feed.url = row['url']
            feed.parser_module = row['parser_module']
            feed.parser_function = row['parser_function']
