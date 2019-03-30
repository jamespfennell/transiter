"""
Service map manager
"""
import datetime
import json

from transiter import models
from transiter.data.dams import servicepatterndam, stopdam
from transiter.services.servicepattern import graphutils


def calculate_realtime_service_maps_for_system(system, route_pks):
    stop_pk_to_station_pk = stopdam.get_stop_pk_to_station_pk_map_in_system(system.id)
    realtime_service_map = None
    for service_map_group in system.service_map_groups:
        if service_map_group.source != 'realtime':
            continue
        realtime_service_map = service_map_group
        break

    if realtime_service_map is None:
        return

    # TODO: waat
    route_pks = set(route_pks)
    routes = [route for route in system.routes if route.pk in route_pks]

    # TODO: make this better - caching for example
    for service_map in list(realtime_service_map.maps):
        if service_map.route_pk in route_pks:
            service_map.group = None

    for route in routes:
        trip_pk_to_path = servicepatterndam.get_trip_pk_to_path_map(route.pk)
        for trip in route.trips:
            if not trip.direction_id:
                trip_pk_to_path.get(trip.pk, []).reverse()
        paths = set()
        for raw_path in trip_pk_to_path.values():
            paths.add(tuple(
                stop_pk_to_station_pk[stop_pk] for stop_pk in raw_path
            ))
        service_map = _construct_service_map(paths)
        service_map.route = route
        service_map.group = realtime_service_map


def calculate_scheduled_service_maps_for_system(system):
    stop_pk_to_station_pk = stopdam.get_stop_pk_to_station_pk_map_in_system(system.id)
    trip_pk_to_stop_pks = servicepatterndam.get_scheduled_trip_pk_to_stop_pks_map()
    route_pk_to_trips = {}

    for trip, start_time, end_time in servicepatterndam.list_scheduled_trips_with_times_in_system():
        trip.start_time = start_time
        trip.end_time = end_time
        if not trip.direction_id:
            trip_pk_to_stop_pks.get(trip.pk, []).reverse()
        trip.path = tuple(
            stop_pk_to_station_pk[stop_pk] for stop_pk in
            trip_pk_to_stop_pks.get(trip.pk, [])
        )
        if trip.route_pk not in route_pk_to_trips:
            route_pk_to_trips[trip.route_pk] = []
        route_pk_to_trips[trip.route_pk].append(trip)

    for service_map_group in system.service_map_groups:
        if service_map_group.source != 'schedule':
            continue
        if service_map_group.conditions is not None:
            conditions = json.loads(service_map_group.conditions)
        else:
            conditions = None
        matcher = _ScheduledTripMatcher(conditions)

        for route_pk, trips in route_pk_to_trips.items():
            path_to_count = {}
            num_trips = 0
            for trip in trips:
                if matcher.match(trip):
                    path_to_count.setdefault(trip.path, 0)
                    path_to_count[trip.path] += 1
                    num_trips += 1

            final_paths = [
                path for path, count in path_to_count.items()
                if count >= num_trips * service_map_group.threshold
            ]
            service_map = _construct_service_map(final_paths)
            service_map.route_pk = route_pk
            service_map.group = service_map_group



"""
def construct_sps_from_gtfs_static_data(
        gtfs_static_parser,
        route_sp_settings=[],
        general_sp_settings=None):
    route_id_to_route = gtfs_static_parser.route_id_to_route
    stop_id_to_stop = gtfs_static_parser.stop_id_to_stop
    trips = gtfs_static_parser.trip_id_to_trip.values()

    # Transform the trips ids
    stop_id_to_station_stop_id = {}
    for stop in stop_id_to_stop.values():
        if not stop.is_station:
            stop_id_to_station_stop_id[stop.id] = stop.parent_stop_id
    # print(stop_id_to_station_stop_id)

    route_id_to_trips = {
        route_id: set() for route_id in route_id_to_route.keys()}
    for trip in trips:
        # TODO: what happens if this is not set?
        if trip.direction_id:
            trip.reverse()

        if trip.route_id in route_id_to_trips:
            route_id_to_trips[trip.route_id].add(trip)

    # TODO: invert the for loops here for an easy optimization
    # Better: split off a new method construct from trips and settings
    for route_id, trips in route_id_to_trips.items():
        route = route_id_to_route[route_id]
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

            service_pattern = _construct_for_static_trips(
                sp_trips, stop_id_to_stop, stop_id_to_station_stop_id)
            service_pattern.name = name
            service_pattern.route = route
            if default:
                route.default_service_pattern = service_pattern
            if regular:
                route.regular_service_pattern = service_pattern
"""


def _construct_service_map(paths):
    sorted_graph = _paths_to_sorted_graph(paths)
    service_pattern = _sorted_graph_to_service_pattern(sorted_graph)
    return service_pattern


def _sorted_graph_to_service_pattern(sorted_graph):
    service_pattern = models.ServicePattern()
    for index, vertex in enumerate(sorted_graph.vertices()):
        sp_vertex = models.ServicePatternVertex()
        sp_vertex.stop_pk = vertex.label
        sp_vertex.service_pattern = service_pattern
        sp_vertex.position = index
    return service_pattern


def _paths_to_sorted_graph(paths):
    if len(paths) == 0:
        return graphutils.graphdatastructs.DirectedPath([])
    if len(paths) == 1:
        unique_element = next(iter(paths))
        return graphutils.graphdatastructs.DirectedPath(unique_element)
    paths = [
        graphutils.graphdatastructs.DirectedPath(path_list) for
        path_list in paths
    ]
    graph = graphutils.pathstitcher.stitch(paths)
    # short circuit if the route_graph is actually a path
    if graph.is_path():
        return graph.cast_to_path()
    return graphutils.topologicalsort.sort(graph)


"""
def _filter_trips_by_conditions(trips, threshold, matching_conditions):
    trip_matcher = _ScheduledTripMatcher(matching_conditions)
    stop_ids_to_trips = {}
    total_count = 0
    for trip in trips:
        if not trip_matcher.match(trip):
            continue
        total_count += 1
        stop_ids = tuple(trip.stop_ids)
        stop_ids_to_trips.setdefault(stop_ids, [])
        stop_ids_to_trips[stop_ids].append(trip)

    filtered_trips = []
    for stop_ids, grouped_trips in stop_ids_to_trips.items():
        if len(grouped_trips) >= threshold * total_count:
            filtered_trips += grouped_trips
    return filtered_trips
"""


class _ScheduledTripMatcher:

    def __init__(self, raw_conds):
        if raw_conds is None:
            raw_conds = {}
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

    _logical_operators = None
    _key_to_function = None
    _key_to_extra_args = None

    @classmethod
    def _convert_raw_condition(cls, key, value):
        # Having these variables as class variables that are populated on the
        # first run is basically a form of caching
        if cls._logical_operators is None:
            cls._logical_operators = {'one_of', 'all_of', 'none_of'}
            cls._key_to_function = {
                'one_of': cls.one_of_factory,
                'all_of': cls.all_of_factory,
                'none_of': cls.none_of_factory,
                'starts_earlier_than': cls.order_factory,
                'starts_later_than': cls.order_factory,
                'ends_earlier_than': cls.order_factory,
                'ends_later_than': cls.order_factory,
                'weekend': cls.weekend_factory,
                'weekday': cls.weekday_factory,
            }
            cls._key_to_extra_args = {
                'starts_earlier_than': ('start_time', True),
                'starts_later_than': ('start_time', False),
                'ends_earlier_than': ('end_time', True),
                'ends_later_than': ('end_time', False),
            }
        if key in cls._logical_operators:
            value = cls._convert_raw_conditions(value)
        try:
            func = cls._key_to_function[key]
        except KeyError:
            raise NotImplementedError
        extra_args = cls._key_to_extra_args.get(key, ())
        return func(value, *extra_args)

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
    def order_factory(value, trip_attr, less_than=True):
        import math
        hour = int(math.floor(value))
        value = (value - hour)*60
        minute = int(math.floor(value))
        value = (value - minute)*60
        second = int(math.floor(value))
        t = datetime.time(hour=hour, minute=minute, second=second)

        def order(trip):
            attr = getattr(trip, trip_attr)
            if attr is None:
                return False
            return (attr < t) == less_than

        return order

    @staticmethod
    def equality_factory(value, trip_attr):
        def equality(trip):
            attr = getattr(trip, trip_attr)
            if attr is None:
                return False
            return attr == value

        def contains(trip):
            attr = getattr(trip, trip_attr)
            if attr is None:
                return False
            return attr in value

        if isinstance(value, list):
            return contains
        return equality

    @staticmethod
    def weekday_factory(value):
        def weekday(trip):
            weekday_cond = (
                trip.service.monday or
                trip.service.tuesday or
                trip.service.wednesday or
                trip.service.thursday or
                trip.service.friday
            )
            weekend_cond = not (trip.service.saturday or trip.service.sunday)
            return (weekday_cond and weekend_cond) == value
        return weekday

    @classmethod
    def weekend_factory(cls, value):
        return cls.weekday_factory(not value)





