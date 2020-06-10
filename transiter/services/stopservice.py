"""
The stop service is used to retrieve information about stops.

In terms of information retrieval, the get_in_system_by_id method is
probably the most important in Transiter. It returns a significant amount
of data, and this is reflected in the amount of code executed.
"""
import collections
import enum
import math
import time
import typing

from transiter import exceptions
from transiter.db import dbconnection, models
from transiter.db.queries import tripqueries, stopqueries, systemqueries
from transiter.services import views, helpers, geography
from transiter.services.servicemap import servicemapmanager
from transiter.services.servicemap.graphutils import datastructures


@dbconnection.unit_of_work
def list_all_in_system(system_id, alerts_detail=None) -> typing.List[views.Stop]:
    system = systemqueries.get_by_id(system_id, only_return_active=True)
    if system is None:
        raise exceptions.IdNotFoundError(models.System, system_id=system_id)

    stops = stopqueries.list_all_in_system(system_id)
    response = list(map(views.Stop.from_model, stops))
    helpers.add_alerts_to_views(
        response, stops, alerts_detail or views.AlertsDetail.NONE,
    )
    return response


@dbconnection.unit_of_work
def geographical_search(
    system_id, latitude, longitude, distance, return_service_maps=True,
) -> typing.List[views.Stop]:
    lower_lat, upper_lat = geography.latitude_bounds(latitude, longitude, distance)
    lower_lon, upper_lon = geography.longitude_bounds(latitude, longitude, distance)
    all_stops = stopqueries.list_all_in_geographical_bounds(
        lower_lat, upper_lat, lower_lon, upper_lon, system_id
    )
    stop_pk_to_distance = {
        stop.pk: geography.distance(
            float(stop.latitude), float(stop.longitude), latitude, longitude,
        )
        for stop in all_stops
    }
    all_stops = list(
        filter(lambda stop_: stop_pk_to_distance[stop_.pk] <= distance, all_stops)
    )
    all_stops.sort(key=lambda stop_: stop_pk_to_distance[stop_.pk])
    if return_service_maps:
        stop_pk_to_service_maps = servicemapmanager.build_stop_pk_to_service_maps_response(
            list(stop.pk for stop in all_stops)
        )
    else:
        stop_pk_to_service_maps = {}

    result = []
    for stop in all_stops:
        result.append(views.Stop.from_model(stop))
        result[-1].distance = int(stop_pk_to_distance[stop.pk])
        if return_service_maps:
            result[-1].service_maps = stop_pk_to_service_maps.get(stop.pk, [])
    return result


@dbconnection.unit_of_work
def list_all_transfers_in_system(
    system_id, from_stop_ids=None, to_stop_ids=None
) -> typing.List[views.Transfer]:
    system = systemqueries.get_by_id(system_id, only_return_active=True)
    if system is None:
        raise exceptions.IdNotFoundError(models.System, system_id=system_id)
    return [
        views.Transfer.from_model(
            transfer,
            views.Stop.from_model(transfer.from_stop),
            views.Stop.from_model(transfer.to_stop),
        )
        for transfer in stopqueries.list_all_transfers_in_system(
            system_id, from_stop_ids=from_stop_ids, to_stop_ids=to_stop_ids
        )
    ]


@dbconnection.unit_of_work
def get_in_system_by_id(
    system_id,
    stop_id,
    return_only_stations=True,
    earliest_time=None,
    latest_time=None,
    minimum_number_of_trips=None,
    include_all_trips_within=None,
    exclude_trips_before=None,
    alerts_detail=None,
):
    """
    Get information about a specific stop.
    """
    stop = stopqueries.get_in_system_by_id(system_id, stop_id)
    if stop is None:
        raise exceptions.IdNotFoundError(
            models.Stop, system_id=system_id, stop_id=stop_id
        )

    stop_tree = _StopTree(stop, stopqueries.list_all_stops_in_stop_tree(stop.pk))
    all_station_pks = set(stop.pk for stop in stop_tree.all_stations())
    transfers = stopqueries.list_all_transfers_at_stops(all_station_pks)

    # The descendant stops are used as the source of trip stop times
    descendant_stop_pks = list(stop.pk for stop in stop_tree.descendents())
    direction_name_matcher = _DirectionNameMatcher(
        stopqueries.list_direction_rules_for_stops(descendant_stop_pks)
    )
    trip_stop_times = stopqueries.list_stop_time_updates_at_stops(
        descendant_stop_pks, earliest_time=earliest_time, latest_time=latest_time,
    )
    trip_pk_to_last_stop = tripqueries.get_trip_pk_to_last_stop_map(
        trip_stop_time.trip.pk for trip_stop_time in trip_stop_times
    )

    # On the other hand, the stop tree graph that is returned consists of all
    # stations in the stop's tree
    stop_pk_to_service_maps_response = servicemapmanager.build_stop_pk_to_service_maps_response(
        all_station_pks.union(transfer.to_stop_pk for transfer in transfers)
    )

    # Using the data retrieved, we then build the response
    response = views.StopLarge.from_model(stop)
    stop_tree_base: views.Stop = _build_stop_tree_response(
        stop_tree, stop_pk_to_service_maps_response, return_only_stations
    )
    response.parent_stop = stop_tree_base.parent_stop
    response.child_stops = stop_tree_base.child_stops
    response.service_maps = stop_tree_base.service_maps
    response.directions = list(direction_name_matcher.all_names())
    response.transfers = _build_transfers_response(
        transfers, stop_pk_to_service_maps_response
    )

    stop_time_filter = _TripStopTimeFilter(
        inclusion_interval_start=exclude_trips_before,
        inclusion_interval_end=include_all_trips_within,
        min_trips_per_direction=minimum_number_of_trips,
    )
    for trip_stop_time in trip_stop_times:
        direction = direction_name_matcher.match(trip_stop_time)
        if stop_time_filter.remove(trip_stop_time, direction):
            continue
        response.stop_times.append(
            _build_trip_stop_time_response(
                trip_stop_time, direction, trip_pk_to_last_stop
            )
        )
    helpers.add_alerts_to_views(
        [response], [stop], alerts_detail or views.AlertsDetail.CAUSE_AND_EFFECT,
    )
    return response


class _TripStopTimeFilter:
    def __init__(
        self, inclusion_interval_start, inclusion_interval_end, min_trips_per_direction
    ):
        self._direction_to_num_trips_so_far = {}
        self._min_trips_per_direction = min_trips_per_direction
        self._inclusion_interval_start = inclusion_interval_start
        self._inclusion_interval_end = inclusion_interval_end
        self._current_time = time.time()

    def remove(self, trip_stop_time: models.TripStopTime, direction):
        result = self._remove_helper(trip_stop_time, direction)
        if not result:
            self._direction_to_num_trips_so_far[direction] = (
                self._direction_to_num_trips_so_far.get(direction, 0) + 1
            )
        return result

    def _remove_helper(self, trip_stop_time: models.TripStopTime, direction):
        trip_time = trip_stop_time.get_time().timestamp()
        # If the trip is before the inclusion interval, remove.
        if self._inclusion_interval_start is not None and (
            trip_time <= self._current_time - float(self._inclusion_interval_start) * 60
        ):
            return True
        # If the trip is within the inclusion interval, include.
        if self._inclusion_interval_end is None or (
            trip_time <= self._current_time + float(self._inclusion_interval_end) * 60
        ):
            return False
        # If an extra trip is needed for this direction, include.
        if self._min_trips_per_direction is not None and self._direction_to_num_trips_so_far.get(
            direction, 0
        ) < int(
            self._min_trips_per_direction
        ):
            return False
        return True


def _build_transfers_response(transfers, stop_pk_to_service_maps_response):
    result = []
    for transfer in transfers:
        to_stop = views.Stop.from_model(
            transfer.to_stop,
            show_system=(transfer.from_stop.system.id != transfer.to_stop.system.id),
        )

        to_stop.service_maps = stop_pk_to_service_maps_response.get(
            transfer.to_stop.pk, []
        )
        result.append(
            views.Transfer.from_model(
                transfer, views.Stop.from_model(transfer.from_stop), to_stop
            )
        )
    return result


def _build_trip_stop_time_response(
    trip_stop_time, direction_name, trip_pk_to_last_stop
):
    """
    Build the response for a specific trip stop time.
    """
    trip = trip_stop_time.trip
    last_stop = trip_pk_to_last_stop[trip.pk]
    result = views.TripStopTime.from_model(trip_stop_time)
    result.direction = direction_name
    result.trip = views.Trip.from_model(trip)
    result.trip.route = views.Route.from_model(trip.route)
    result.trip.last_stop = views.Stop.from_model(last_stop)
    return result


class _StopTree:
    """
    An class to represent the stop tree and desired operations on it.

    The main motivation of this data structure is to get around unavoidable lazy loading
    of tree data structures in SQLAlchemy (in fact, ORMs in general). Lazy loading means
    traversing the stops tree by using models.Stop.parent and models.Stop.children is
    inefficient: N SQL queries will be emitted where N is the number of stops in the
    tree.

    This data structure under the hood uses an adjacency list method of traversing the
    tree. The adjacency lists are constructed when the object is initialized using the
    collection of all stops in the tree. In Postgres, at least, the collection of all
    stops can be retrieved in one recursive SQL query.
    """

    class TraversalMode(enum.Enum):
        """
        Ways in which the tree can be traversed starting from the base node.
        """

        DESCENDANTS = 0
        ALL = 1

    def __init__(self, base: models.Stop, stops: typing.Iterable[models.Stop]):
        """
        Initialize a new StopTrue.

        :param base: the base of the tree. This is not necessarily the root.
        :param stops: an iterable of all stops in the tree. If stops are missing from
                      this iterable, and error will be raised.
        """
        self._base = base
        self._stop_pk_to_stop = {stop.pk: stop for stop in stops}
        self._stop_pk_to_parent_pk = {
            stop.pk: stop.parent_stop_pk for stop in self._stop_pk_to_stop.values()
        }
        self._stop_pk_to_child_pks = collections.defaultdict(list)
        for stop_pk, parent_pk in self._stop_pk_to_parent_pk.items():
            if parent_pk is not None:
                self._stop_pk_to_child_pks[parent_pk].append(stop_pk)

    def descendents(self) -> typing.Iterator[models.Stop]:
        """
        Get all descendents of the base stop, including the stop itself.
        """
        yield from self._dfs_traverse(_StopTree.TraversalMode.DESCENDANTS, False)

    def all_stations(self) -> typing.Iterator[models.Stop]:
        """
        Get all stations in the tree.

        The base stop is always returned irrespective of whether it is a station.
        """
        yield from self._dfs_traverse(_StopTree.TraversalMode.ALL, True)

    _T = typing.TypeVar("_T")

    def apply_function(
        self,
        function: typing.Callable[
            [models.Stop, typing.Optional[_T], typing.List[_T]], _T
        ],
        only_stations: bool,
    ) -> _T:
        """
        The method applies a function to each node in the traversal. It uses a
        depth-first search, so when evaluating the function at a given node
        the results of evaluating the function at the nodes the next level
        deep are available. The return of this function is the value of the node
        function at the base.

        The function signature is described above. The arguments passed to it are:

        - stop: the current node being evaluated
        - parent_result: the result of the function applied to the parent.
                         If the parent hasn't been visited in the traversal yet, this
                         will be None.
        - children_results: a list of results for the function applied to the children
                            of the current stop. Given the DFS nature of the traversal,
                            at most one child will have not been visited when the parent
                            is visited. The result of this child will, of course, be
                            missing from this list.
        """
        stop_pk_to_response = {}
        for stop in self._dfs_traverse(
            _StopTree.TraversalMode.ALL, only_stations=only_stations
        ):
            parent_response = stop_pk_to_response.get(stop.parent_stop_pk)
            children_responses = [
                stop_pk_to_response[child_pk]
                for child_pk in self._stop_pk_to_child_pks[stop.pk]
                if child_pk in stop_pk_to_response
            ]
            stop_pk_to_response[stop.pk] = function(
                stop, parent_response, children_responses
            )
        return stop_pk_to_response[self._base.pk]

    def _dfs_traverse(
        self, traversal_mode, only_stations=False
    ) -> typing.Iterator[models.Stop]:

        stack = datastructures.Stack()
        stack.push((self._base.pk, False))
        visited_pks = set()
        visited_pks.add(self._base.pk)

        while len(stack) > 0:
            stop_pk, neighbors_added = stack.pop()
            if neighbors_added:
                stop = self._stop_pk_to_stop[stop_pk]
                if only_stations and not stop.is_station() and stop.pk != self._base.pk:
                    continue
                yield stop
                continue

            stack.push((stop_pk, True))
            neighbors = list(self._stop_pk_to_child_pks[stop_pk])
            neighbors.sort(reverse=True)  # Give the traversal a deterministic result
            parent_pk = self._stop_pk_to_parent_pk[stop_pk]
            if parent_pk is not None and (
                stop_pk != self._base.pk
                or traversal_mode is _StopTree.TraversalMode.ALL
            ):
                neighbors.append(parent_pk)
            for neighbor in neighbors:
                if neighbor in visited_pks:
                    continue
                visited_pks.add(neighbor)
                stack.push((neighbor, False))


def _build_stop_tree_response(
    stop_tree, stop_pk_to_service_maps_response, return_only_stations
):
    """
    Build the stop tree response.

    The response consists of a nested dictionary representing the stop tree
    with the given base as the starting point of the representation. A given
    stop in the dictionary can contain 'parent_stop' and 'child_stops'
    keys which point to relevant related stops in the tree.

    Each stop appearing also contains its short representation, its service
    map representation and, optionally, a link to the stop.
    """

    def node_function(stop, parent_return, children_return):
        response = views.Stop.from_model(stop)
        response.service_maps = stop_pk_to_service_maps_response[stop.pk]
        if parent_return is not None:
            response.parent_stop = parent_return
        if stop.parent_stop_pk is None:
            response.parent_stop = None
        if children_return is not None:
            response.child_stops = children_return
        return response

    return stop_tree.apply_function(node_function, only_stations=return_only_stations)


class _DirectionNameMatcher:
    """
    Object to find the direction name associated to a particular trip at
    a particular stop.
    """

    def __init__(self, rules):
        """
        Initialize a new matcher.

        :param rules: the rules to be used in the matcher.
        :type rules: iterable of DirectionRule models.
        """
        self._rules = sorted(rules, key=lambda rule: rule.priority)
        self._cache = {}

    def all_names(self):
        """
        Get all of the direction names in the matcher.

        :return: list of names
        :rtype: list of strings
        """
        print(self._rules)
        return {rule.name for rule in self._rules}

    def match(self, trip_stop_time):
        """
        Find the direction name associate to the TripStopTime by matching
        the appropriate rule.

        :param trip_stop_time: the TripStopTime
        :return: the direction name
        """
        cache_key = (
            trip_stop_time.stop_pk,
            trip_stop_time.trip.direction_id,
            trip_stop_time.track,
        )
        if cache_key not in self._cache:
            self._cache[cache_key] = None
            for rule in self._rules:
                if rule.stop_pk != cache_key[0]:
                    continue
                if rule.direction_id is not None and rule.direction_id != cache_key[1]:
                    continue
                if rule.track is not None and rule.track != cache_key[2]:
                    continue
                self._cache[cache_key] = rule.name
                break

        return self._cache[cache_key]
