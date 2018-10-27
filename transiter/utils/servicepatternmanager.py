"""
ALGO

USE GTFS STATIC! It does everything!

Step 3: for each route, pass each RawTrip through the matchers for that route
    to get a set of RawTrips for that matchers. By defining a hash function
    that only takes the list of stops, we eliminate duplicates automatically!
"""

from transiter.utils import graphutils
from transiter.database import models

# Todo just input the gtfsparser
def construct_service_patterns_from_static_trips(
        route_id_to_route,
        stop_id_to_stop,
        trips,
        route_sp_settings=None,
        general_sp_settings=None):

    if route_sp_settings is None:
        route_sp_settings = []

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
        for sp_setting in route_sp_settings:
            name = sp_setting.get('name', None)
            default = sp_setting.get('default', False)
            regular = sp_setting.get('regular', False)
            threshold = sp_setting.get('threshold', 0)
            conditions = sp_setting.get('conditions', None)

            if conditions is not None:
                sp_trips = _filter_trips_by_conditions(trips, threshold, conditions)
            else:
                sp_trips = trips
            print(route_id)
            print(len(trips))
            print(len(sp_trips))

            service_pattern = _construct_for_static_trips(sp_trips, stop_id_to_stop)
            service_pattern.name = name
            service_pattern.route = route
            if default:
                route.default_service_pattern = service_pattern
            if regular:
                route.regular_service_pattern = service_pattern


def _construct_for_static_trips(trips, stop_id_to_stop):
    path_lists = set()
    for trip in trips:
        path_lists.add(tuple(trip.stop_ids))
    sorted_graph = _path_lists_to_sorted_graph(path_lists)
    service_pattern = _sorted_graph_to_service_pattern(sorted_graph, stop_id_to_stop)
    return service_pattern


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


def _filter_trips_by_conditions(trips, threshold, matching_conditions):
    trip_matcher = _TripMatcher(matching_conditions)
    stop_ids_to_trip = {}
    stop_ids_to_count = {}
    total_count = len(trips)
    for trip in trips:
        if not trip_matcher.match(trip):
            continue
        stop_ids = tuple(trip.stop_ids)
        stop_ids_to_trip.setdefault(stop_ids, trip)
        stop_ids_to_count.setdefault(stop_ids, 0)
        stop_ids_to_count[stop_ids] += 1

    filtered_trips = []
    for stop_ids, count in stop_ids_to_count.items():
        if count >= threshold * total_count:
            filtered_trips.append(stop_ids_to_trip[stop_ids])
    return filtered_trips


class _TripMatcher:

    def __init__(self, raw_conds):
        self._primary_conditions = self._convert_raw_conditions(raw_conds)

    def match(self, trip):
        for condition in self._primary_conditions:
            if not condition(trip):
                return False
        return True

    @classmethod
    def _convert_raw_conditions(cls, dictionary):
        conditions = []
        for key, value in dictionary.items():
            conditions.append(cls._convert_raw_condition(key, value))
        return conditions

    @classmethod
    def _convert_raw_condition(cls, key, value):
        print(key, value)
        # TODO Can the following switch like statements be converted to a dict?
        if key == 'one_of':
            return cls.one_of_factory(cls._convert_raw_conditions(value))
        if key == 'all_of':
            return cls.all_of_factory(cls._convert_raw_conditions(value))
        if key == 'none_of':
            return cls.none_of_factory(cls._convert_raw_conditions(value))
        if key == 'weekday':
            return cls.weekday
        if key == 'weekend':
            return cls.weekend
        if key == 'starts_earlier_than':
            return cls.order_factory('start_time', value, True)
        if key == 'starts_later_than':
            return cls.order_factory('start_time', value, False)
        if key == 'ends_earlier_than':
            return cls.order_factory('end_time', value, True)
        if key == 'ends_later_than':
            return cls.order_factory('end_time', value, False)
        raise NotImplementedError

    @staticmethod
    def one_of_factory(conditions):
        def one_of(trip):
            for condition in conditions:
                if condition(trip):
                    return True
            return False
        return one_of

    @staticmethod
    def none_of_factory(conditions):
        def none_of(trip):
            for condition in conditions:
                if condition(trip):
                    return False
            return True
        return none_of

    @staticmethod
    def all_of_factory(conditions):
        def all_of(trip):
            for condition in conditions:
                if not condition(trip):
                    return False
            return True
        return all_of

    @staticmethod
    def order_factory(trip_attr, value, less_than=True):
        def order(trip):
            return (getattr(trip, trip_attr) < value) == less_than
        return order

    @staticmethod
    def equality_factory(trip_attr, value):
        def equality(trip):
            return getattr(trip, trip_attr) == value
        return equality

    @staticmethod
    def weekday(trip):
        weekday_cond = trip.monday or trip.tuesday or trip.wednesday or trip.thursday or trip.friday
        weekend_cond = not (trip.saturday or trip.sunday)
        return weekday_cond and weekend_cond

    @classmethod
    def weekend(cls, trip):
        return not cls.weekday(trip)















yaml = """

route_service_patterns:

   - name: weekday_night
     usual: true
     threshold: 0.05
     conditions:
       weekday: true
       one_of:
         starts_earlier_than: 7
         starts_later_than: 20
         
   - name: weekday_day
     usual: true
     threshold: 0.05
     conditions:
       weekday: true
       starts_later_than: 7
       starts_earlier_than: 20
         
         
         
route_service_patterns:
 - weekday_night:
   - usual: true
   - threshold: 0.05
   - conditions:
     - weekday 
     - one_of:
       - starts_earlier_than: 7
       - starts_later_than: 20
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

