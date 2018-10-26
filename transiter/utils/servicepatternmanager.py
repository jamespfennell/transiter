"""
ALGO

USE GTFS STATIC! It does everything!

Step 3: for each route, pass each RawTrip through the matchers for that route
    to get a set of RawTrips for that matchers. By defining a hash function
    that only takes the list of stops, we eliminate duplicates automatically!
"""

from transiter.utils import graphutils
from transiter.database import models


def construct_service_patterns_from_static_trips(
        route_id_to_route,
        stop_id_to_stop,
        trips,
        settings):

    route_id_to_trips = {
        route_id: set() for route_id in route_id_to_route.keys()}
    for trip in trips:
        if trip.direction_id:
            trip.reverse()
        route_id_to_trips[trip.route_id].add(trip)

    for route_id, trips in route_id_to_trips.items():
        route = route_id_to_route.get(route_id, None)
        if route is None:
            continue
        service_patterns = _construct_for_static_trips(trips, stop_id_to_stop)
        for service_pattern in service_patterns:
            service_pattern.route = route
            route.default_service_pattern = service_pattern


def _construct_for_static_trips(trips, stop_id_to_stop):
    path_lists = set()
    for trip in trips:
        path_lists.add(tuple(trip.stop_ids))
    sorted_graph = _path_lists_to_sorted_graph(path_lists)
    service_pattern = _sorted_graph_to_service_pattern(sorted_graph, stop_id_to_stop)
    return [service_pattern]


def _sorted_graph_to_service_pattern(sorted_graph, stop_id_to_stop):
    service_pattern = models.ServicePattern()
    for index, vertex in enumerate(sorted_graph.vertices()):
        stop_id = vertex.label
        stop = stop_id_to_stop[stop_id]
        sp_vertex = models.ServicePatternVertex()
        sp_vertex.stop = stop
        sp_vertex.service_pattern = service_pattern
        sp_vertex.position = index
    return service_pattern


def _path_lists_to_sorted_graph(path_lists):
    if len(path_lists) == 0:
        return graphutils.graphdatastructs.DirectedPath([])
    if len(path_lists) == 1:
        unique_element = next(iter(path_lists))
        return graphutils.graphdatastructs.DirectedPath(unique_element)
    paths = [
        graphutils.graphdatastructs.DirectedPath(path_list) for
        path_list in path_lists
    ]
    graph = graphutils.pathstitcher.stitch(paths)
    # short circuit if the route_graph is actually a path
    if graph.is_path():
        return graph.cast_to_path()
    return graphutils.topologicalsort.sort(graph)


"""
class ServicePatternTripsMatcher:
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


def weekday_night(trip):


def weekday_day(trip):


def weekend(trip):
    return trip.saturday and trip.sunday


def all_times(trip):
    return True


def starts_earlier_than(trip, hours):


def starts_later_than(trip, hours):

-all_of

-not

-weekend
"""

yaml = """
route_service_patterns:
    - weekday_night:
        - usual: true
        - threshold: 0.05
        - conditions:
            - weekday
            - one_of:
                - starts_earlier_than: 7
                - starts_later_than: 20
    - weekday_day:
        - weekday
        - starts_later_than: 7
        - starts_earlier_than: 20
    - weekend:
        - weekend
    - all_times:
        - default: true
        
        
        or ends_earlier_than
            -7
        -starts_later_than
            -21
"""

"""
route_id: L

all_times_matcher = ServicePatternTripsMatcher('all_times', 0.05, all_times)

"""

