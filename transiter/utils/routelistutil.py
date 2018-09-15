import csv
import re
from . import graphutils


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

def construct_route_lists_from_stop_times_file(system, stop_times_file_path):
    # This is NYC subway specific regex - should be abstracted away into
    # a sessions file or something
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
