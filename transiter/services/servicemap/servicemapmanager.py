"""
Service map manager has responsibility for constructing and displaying service
maps
"""
import datetime
import json
import logging
from typing import List, Set, Tuple
from transiter import models
from transiter.data.dams import scheduledam, servicemapdam, stopdam, tripdam
from transiter.services.servicemap import graphutils, conditions

logger = logging.getLogger(__name__)


def build_stop_pk_to_service_maps_response(stop_pks):
    """
    Build the service maps response used in the stop service.

    :param stop_pks: the PKs of the stops to construct it for.
    :return: a map of stop PK to the response
    """
    stop_pks = list(stop_pks)
    stop_pk_to_service_map_group_id_to_routes = servicemapdam.get_stop_pk_to_group_id_to_routes_map(
        stop_pks
    )
    stop_pk_to_service_maps_response = {}
    for stop_pk in stop_pks:
        group_id_to_routes = stop_pk_to_service_map_group_id_to_routes[stop_pk]
        stop_pk_to_service_maps_response[stop_pk] = [
            {"group_id": group_id, "routes": [route.short_repr() for route in routes]}
            for group_id, routes in group_id_to_routes.items()
        ]
    return stop_pk_to_service_maps_response


def calculate_realtime_service_map_for_route(route):
    """
    Build the realtime service map for a route

    :param route: the route
    :return: nothing; the service map is persisted in the database
    """
    # First find the realtime service map group, if it exists.
    realtime_service_map = None
    for service_map_group in route.system.service_map_groups:
        if service_map_group.source != models.ServiceMapGroup.ServiceMapSource.REALTIME:
            continue
        realtime_service_map = service_map_group
        break
    if realtime_service_map is None:
        return

    # Delete the old service map for this route. This works by using SQL
    # Alchemy's delete orphan cascade.
    for service_map in list(realtime_service_map.maps):
        if service_map.route_pk == route.pk:
            service_map.group = None
            break

    # Now actually build the map.
    stop_pk_to_station_pk = stopdam.get_stop_pk_to_station_pk_map_in_system(
        route.system.id
    )
    trip_pk_to_path = tripdam.get_trip_pk_to_path_map(route.pk)
    paths = set()
    for trip in route.trips:
        path = trip_pk_to_path.get(trip.pk, [])
        if not trip.direction_id:
            path.reverse()
        paths.add(tuple(stop_pk_to_station_pk[stop_pk] for stop_pk in path))
    logger.info("Building realtime service map for route {}.".format(route.id))
    try:
        service_map = _build_service_map_from_paths(paths)
    except graphutils.topologicalsort.ImpossibleToTopologicallySortGraph:
        logger.exception(
            "Could not topologically sort:\n{}".format(
                json.dumps(list(paths))
            )  # list(paths), indent=2))
        )
        raise
    service_map.route = route
    service_map.group = realtime_service_map


def calculate_scheduled_service_maps_for_system(system):
    """
    Build the schedule service maps for a system

    :param system: the system
    :return: nothing; the service maps are persisted in the database
    """
    stop_pk_to_station_pk = stopdam.get_stop_pk_to_station_pk_map_in_system(system.id)
    trip_pk_to_stop_pks = scheduledam.get_scheduled_trip_pk_to_path_in_system(system.pk)
    route_pk_to_trips = {}

    for (
        trip,
        start_time,
        end_time,
    ) in scheduledam.list_scheduled_trips_with_times_in_system(system.pk):
        trip.start_time = start_time
        trip.end_time = end_time
        if not trip.direction_id:
            trip_pk_to_stop_pks.get(trip.pk, []).reverse()
        trip.path = tuple(
            stop_pk_to_station_pk[stop_pk]
            for stop_pk in trip_pk_to_stop_pks.get(trip.pk, [])
        )
        if trip.route_pk not in route_pk_to_trips:
            route_pk_to_trips[trip.route_pk] = []
        route_pk_to_trips[trip.route_pk].append(trip)

    for service_map_group in system.service_map_groups:
        if service_map_group.source != models.ServiceMapGroup.ServiceMapSource.SCHEDULE:
            continue
        # Delete the old maps, using SQL Alchemy's delete-orphan cascade
        service_map_group.maps = []
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

            final_paths = {
                path
                for path, count in path_to_count.items()
                if count >= num_trips * service_map_group.threshold
            }
            service_map = _build_service_map_from_paths(final_paths)
            service_map.route_pk = route_pk
            service_map.group = service_map_group


def _build_service_map_from_paths(paths):
    """
    Given a list of paths build the service map.
    """
    labels = []
    for graph in _build_sorted_graph_from_paths(paths):
        for node in graph.nodes():
            labels.append(node.label)
    return _convert_sorted_graph_to_service_pattern(labels)


def _convert_sorted_graph_to_service_pattern(sorted_labels):
    """
    Convert a sorted graph object to a service map object.
    """
    service_pattern = models.ServiceMap()
    for index, label in enumerate(sorted_labels):
        sp_vertex = models.ServiceMapVertex()
        sp_vertex.stop_pk = label
        sp_vertex.map = service_pattern
        sp_vertex.position = index
    return service_pattern


def _build_sorted_graph_from_paths(
    paths: Set[Tuple],
) -> List[graphutils.datastructures.AbstractGraph]:
    """
    Given a list of paths build the sorted graph.
    """
    if len(paths) == 0:
        return [graphutils.datastructures.Graph()]
    if len(paths) == 1:
        unique_path = next(iter(paths))
        return [graphutils.datastructures.Path.build_from_label_list(unique_path)]
    additional_nodes = set()
    edge_tuples = set()
    for path in paths:
        if len(path) == 1:
            additional_nodes.add(path[0])
            continue
        for i in range(len(path) - 1):
            edge_tuples.add((path[i], path[i + 1]))
    graph = graphutils.datastructures.MutableGraph.build_from_edge_label_tuples(
        edge_tuples, additional_nodes
    )
    return list(
        map(
            graphutils.topologicalsort.tgt_sort,
            graphutils.operations.split_into_connected_components(graph),
        )
    )


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
            cls._logical_operators = {
                conditions.ALL_OF,
                conditions.NONE_OF,
                conditions.ONE_OF,
            }
            cls._key_to_function = {
                conditions.ALL_OF: cls.all_of_factory,
                conditions.ENDS_EARLIER_THAN: cls.order_factory,
                conditions.ENDS_LATER_THAN: cls.order_factory,
                conditions.STARTS_EARLIER_THAN: cls.order_factory,
                conditions.NONE_OF: cls.none_of_factory,
                conditions.ONE_OF: cls.one_of_factory,
                conditions.STARTS_LATER_THAN: cls.order_factory,
                conditions.WEEKDAY: cls.weekday_factory,
                conditions.WEEKEND: cls.weekend_factory,
            }
            cls._key_to_extra_args = {
                conditions.ENDS_EARLIER_THAN: ("end_time", True),
                conditions.ENDS_LATER_THAN: ("end_time", False),
                conditions.STARTS_EARLIER_THAN: ("start_time", True),
                conditions.STARTS_LATER_THAN: ("start_time", False),
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
        value = (value - hour) * 60
        minute = int(math.floor(value))
        value = (value - minute) * 60
        second = int(math.floor(value))
        t = datetime.time(hour=hour, minute=minute, second=second)

        def order(trip):
            attr = getattr(trip, trip_attr)
            if attr is None:
                return False
            return (attr < t) == less_than

        return order

    @staticmethod
    def weekday_factory(value):
        def weekday(trip):
            weekday_cond = (
                trip.service.monday
                or trip.service.tuesday
                or trip.service.wednesday
                or trip.service.thursday
                or trip.service.friday
            )
            weekend_cond = not (trip.service.saturday or trip.service.sunday)
            return (weekday_cond and weekend_cond) == value

        return weekday

    @classmethod
    def weekend_factory(cls, value):
        return cls.weekday_factory(not value)
