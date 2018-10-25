"""
ALGO

USE GTFS STATIC! It does everything!

Step 1: Reverse all trips to have direction_id = 0
Step 2: Group by route
Step 3: for each route, pass each RawTrip through the matchers for that route
    to get a set of RawTrips for that matchers. By defining a hash function
    that only takes the list of stops, we eliminate duplicates automatically!
Step 4: For each matcher, feed it into the graph utils to construct the
    topologically sorted graph
Step 5: call the function that converts this graph into the DB data structures
(Would also be good to write the inverse function)
"""


import csv
import re
from . import graphutils

from transiter.database.models import ServicePattern
from transiter.database.models import ServicePatternVertex
from transiter.database.daos import service_pattern_dao


def generate_service_patterns_from_gtfs_static_data(
        system,
        stop_times_file_path,
        routes_by_route_id,
        stops_by_stop_id):

    print('Here!')
    d = populate_raw_trips_from_stop_times_file(stop_times_file_path)
    print(d)
    exit()

    route_lists = construct_route_lists_from_stop_times_file(
        system,
        stop_times_file_path
    )
    for (route_id, route_list) in route_lists.items():
        route = routes_by_route_id[route_id]
        position = 0

        service_pattern = service_pattern_dao.create()
        #service_pattern.route = route
        route.default_service_pattern = service_pattern

        for stop_id in route_list:

            route_list_entry = service_pattern_dao.temp_create_route_list_entry()
            route_list_entry.route = route
            route_list_entry.stop = stops_by_stop_id[stop_id]
            route_list_entry.position = position

            vertex = service_pattern_dao.create_vertex()
            vertex.service_pattern = service_pattern
            vertex.stop = stops_by_stop_id[stop_id]
            vertex.position = position

            position += 1


# STEP ONE
def populate_raw_trips_from_stop_times_file(stop_times_file_path):
    current_raw_trip_id = None
    current_raw_trip = None
    route_id_to_raw_trip = {}
    with open(stop_times_file_path) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for index, row in enumerate(csv_reader):
            raw_trip_id = row['trip_id']
            if raw_trip_id != current_raw_trip_id:
                if index > 100:
                    break
                current_raw_trip_id = raw_trip_id

                raw_trip = RawTrip()
                # TODO: what if there's an exception here?
                raw_trip.add_raw_trip_id(raw_trip_id)

                if raw_trip.route_id not in route_id_to_raw_trip:
                    route_id_to_raw_trip[raw_trip.route_id] = []
                route_id_to_raw_trip[raw_trip.route_id].append(raw_trip)

                current_raw_trip = raw_trip

            if current_raw_trip is None:
                continue

            # TODO: what if there's an exception here?
            current_raw_trip.add_stop(row['stop_id'], row['arrival_time'],
                                  row['departure_time'])

    return route_id_to_raw_trip


class RawTrip:
    # TODO: move add_raw_trip_id logic to  __init__
    def __init__(self):
        self.metadata = {}
        self.stop_ids = []
        self.start_time = None
        self.end_time = None
        self.trip_id = None
        self.route_id = None

    def add_raw_trip_id(self, raw_trip_id):
        trip_id_to_data_regex_string = \
            '^(?:SIR-)?[A-Z0-9]{6,8}-[A-Z0-9]{4,5}-(?P<category>Weekday|Sunday|Saturday)-' + \
            '[0-9]{2}_[0-9]{6}_(?P<route_id>[A-Z0-9]+)..' + \
            '(?P<direction>[SN])[A-Z0-9]{3,6}$'
        trip_data = re.match(trip_id_to_data_regex_string, raw_trip_id)
        if trip_data is None:
            print(raw_trip_id)
            exit()
        self.metadata = trip_data.groupdict()
        print(raw_trip_id)
        print(self.metadata)
        self.route_id = self.metadata.get('route_id', None)

    def add_stop(self, raw_stop_id, arrival_time, departure_time):

        if len(self.stop_ids) == 0:
            print(arrival_time)
            self.start_time = departure_time
            self.end_time = departure_time
        else:
            self.end_time = arrival_time
        stop_id_to_data_regex_string = \
            '^(?P<stop_id>[A-Z0-9]{3})(?P<direction>[SN])$'
        stop_id_data = re.match(stop_id_to_data_regex_string, raw_stop_id)
        self.stop_ids.append(stop_id_data.group('stop_id'))

    def reverse(self):
        self.stop_ids.reverse()


class Trip:
    def __init__(self):
        self.stops = []
        pass


def _construct_route_list_from_path_lists(path_lists):
    if len(path_lists) == 0:
        return []
    if len(path_lists) == 1:
        return path_lists[0]
    paths = [graphutils.graphdatastructs.DirectedPath(path_list) for
        path_list in path_lists]
    route_graph = graphutils.pathstitcher.stitch(paths)
    # short circuit if the route_graph is actually a path
    if route_graph.is_path():
        return [vertex.label for vertex in route_graph.cast_to_path().vertices()]
    #return
    sorted_route_graph = graphutils.topologicalsort.sort(route_graph)
    return [vertex.label for vertex in sorted_route_graph.vertices()]


def construct_route_list_from_route_db_data(route):

    pass


class ServicePatternTripsMatcher:
    """
    Used to match trips in the stop times with a service pattern.
    """
    def __init__(self, name, threshold, matcher_func):
        self._name = name
        self._threshold = threshold
        self._matcher_func = matcher_func
        self._trips = []

    def match(self, trip):
        if self._matcher_func(trip):
            self._trips.append(trip)


def daytime(data):
    if data.get('category', None) != 'Weekday':
        return False
    start_hour = data.get('start_hour', -1)
    end_hour = data.get('end_hour', -1)
    if 7 < start_hour and end_hour < 21:
        return True
    return False


daytime_matcher = ServicePatternTripsMatcher('daytime', 0.05, daytime)


def all_times(data):
    return True


all_times_matcher = ServicePatternTripsMatcher('all_times', 0.05, all_times)


def construct_route_lists_from_stop_times_file(system, stop_times_file_path):
    # This is NYC subway specific regex - should be abstracted away into
    # a sessions file or something

    # Use arrival_time to filter
    trip_id_to_data_regex_string = \
        '^(SIR-)?[A-Z0-9]{6,8}-[A-Z0-9]{4,5}-(?P<category>Weekday|Sunday|Saturday)-' + \
        '[0-9]{2}_[0-9]{6}_(?P<route_id>[A-Z0-9]+)..' + \
        '(?P<direction>[SN])[A-Z0-9]{3,6}$'
    stop_id_to_data_regex_string = \
        '^(?P<stop_id>[A-Z0-9]{3})(?P<direction>[SN])$'
    print('Hllo')

    trip_id_to_data_regex = re.compile(trip_id_to_data_regex_string)
    stop_id_to_data_regex = re.compile(stop_id_to_data_regex_string)

    current_trip_id = None
    current_trip = None
    route_id_to_trips = {}
    print('Read trip schedules file')
    with open(stop_times_file_path) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        num_rows = 0
        for row in csv_reader:
            num_rows += 1
            trip_id = row['trip_id']
            stop_id = row['stop_id']
            if trip_id != current_trip_id:
                current_trip_id = trip_id
                # right now we ignore stop sequence and assume it is increasing
                trip_id_data = trip_id_to_data_regex.search(row['trip_id'])
                if not trip_id_data:
                    print('Could not interpret trip_id "{}"'.format(row['trip_id']))
                    current_trip = None
                    continue
                current_trip = Trip()
                current_trip.route_id = trip_id_data.group('route_id')
                #temp short circuit for testing
                #if current_trip.route_id != '1':
                #    current_trip = None
                #    continue
                current_trip.direction = trip_id_data.group('direction')
                current_trip.category = trip_id_data.group('category')
                if current_trip.route_id not in route_id_to_trips:
                    route_id_to_trips[current_trip.route_id] = {}
                route_id_to_trips[current_trip.route_id][trip_id] = current_trip

            if current_trip is None:
                continue

            stop_id_data = stop_id_to_data_regex.search(row['stop_id'])
            if not stop_id_data:
                print('Could not interpret stop_id "{}"'.format(row['stop_id']))
                continue

            current_trip.stops.append(stop_id_data.group('stop_id'))
    print('Read {} lines'.format(num_rows))
    route_id_to_route_list = {}
    for route_id, trips in route_id_to_trips.items():
        print('Constructing list for route {}'.format(route_id))
        trip_hash_to_num_trips = {}
        trip_hash_to_trip = {}
        num_trips = 0
        for trip in trips.values():
            # TODO: construct graphs for each categeory
            #if trip.category != 'Weekday':
            #    continue
            if trip.direction == 'N':
                trip.stops.reverse()
                trip.directioin = 'S'
            trip_hash = ''.join(trip.stops)
            if trip_hash not in trip_hash_to_num_trips:
                trip_hash_to_num_trips[trip_hash] = 0
                trip_hash_to_trip[trip_hash] = trip
            trip_hash_to_num_trips[trip_hash] += 1
            num_trips += 1

        ignore_threshold = num_trips*0.0

        for trip_hash, number in trip_hash_to_num_trips.items():
            if number < ignore_threshold:
                del trip_hash_to_trip[trip_hash]

        route_trips = [trip.stops for trip in trip_hash_to_trip.values()]

        route_id_to_route_list[route_id] = _construct_route_list_from_path_lists(route_trips)

    return route_id_to_route_list
