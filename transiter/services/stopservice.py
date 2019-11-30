"""
The stop service is used to retrieve information about stops.

In terms of information retrieval, the get_in_system_by_id method is
probably the most important in Transiter. It returns a significant amount
of data, and this is reflected in the amount of code executed.
"""
import enum
import itertools
import time

from transiter import exceptions, models
from transiter.data import dbconnection
from transiter.data.dams import stopdam, tripdam, systemdam
from transiter.services import links
from transiter.services.servicemap import servicemapmanager


@dbconnection.unit_of_work
def list_all_in_system(system_id, return_links=True):
    """
    Get information on all stops in a specific system.

    :param system_id: the system ID
    :type system_id: str
    :param return_links: whether to return links
    :type return_links: bool
    :return: a list of dictionaries, one for each stop, containing the stop's
             short representation and optionally a link.
    """
    system = systemdam.get_by_id(system_id)
    if system is None:
        raise exceptions.IdNotFoundError

    response = []
    for stop in stopdam.list_all_in_system(system_id):
        stop_response = stop.short_repr()
        if return_links:
            stop_response["href"] = links.StopEntityLink(stop)
        response.append(stop_response)
    return response


@dbconnection.unit_of_work
def get_in_system_by_id(
    system_id,
    stop_id,
    return_links=True,
    return_only_stations=True,
    earliest_time=None,
    latest_time=None,
    minimum_number_of_trips=None,
    include_all_trips_within=None,
    exclude_trips_before=None,
):
    """
    Get information about a specific stop.

    :param system_id: the system ID
    :param stop_id: the stop ID
    :param return_links: whether to return links
    :param return_only_stations: whether to return only stations in the stops
                                 graph
    """

    stop = stopdam.get_in_system_by_id(system_id, stop_id)
    if stop is None:
        raise exceptions.IdNotFoundError

    # The descendant stops are used as the source of trip stop times
    descendant_stops = _get_stop_descendants(stop)
    direction_name_matcher = _DirectionNameMatcher(
        itertools.chain.from_iterable(stop.direction_rules for stop in descendant_stops)
    )
    trip_stop_times = stopdam.list_stop_time_updates_at_stops(
        (stop.pk for stop in descendant_stops),
        earliest_time=earliest_time,
        latest_time=latest_time,
    )
    trip_pk_to_last_stop = tripdam.get_trip_pk_to_last_stop_map(
        trip_stop_time.trip.pk for trip_stop_time in trip_stop_times
    )

    # On the other hand, the stop tree graph that is returned consists of all
    # stations in the stop's tree
    stop_pk_to_service_maps_response = servicemapmanager.build_stop_pk_to_service_maps_response(
        stop.pk for stop in _get_all_stations(stop)
    )

    # Using the data retrieved, we then build the response
    response = _build_stop_tree_response(
        stop, stop_pk_to_service_maps_response, return_links, return_only_stations
    )
    response.update(stop.long_repr())
    response.update(
        {
            "directions": list(direction_name_matcher.all_names()),
            "stop_time_updates": [],
        }
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
        response["stop_time_updates"].append(
            _build_trip_stop_time_response(
                trip_stop_time, direction, trip_pk_to_last_stop, return_links
            )
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


def _build_trip_stop_time_response(
    trip_stop_time, direction_name, trip_pk_to_last_stop, return_links
):
    """
    Build the response for a specific trip stop time.

    :param trip_stop_time: the trip stop time
    :param direction_name: the direction name
    :param trip_pk_to_last_stop: map giving the last stop of trips
    :param return_links: whether to return links
    :return:
    """
    trip = trip_stop_time.trip
    last_stop = trip_pk_to_last_stop[trip.pk]
    trip_stop_time_response = {
        "stop_id": trip_stop_time.stop.id,
        "direction": direction_name,
        **trip_stop_time.short_repr(),
        "trip": {
            **trip_stop_time.trip.long_repr(),
            "route": trip_stop_time.trip.route.short_repr(),
            "last_stop": last_stop.short_repr(),
        },
    }
    if return_links:
        trip_stop_time_response["trip"]["href"] = links.TripEntityLink(
            trip_stop_time.trip
        )
        trip_stop_time_response["trip"]["route"]["href"] = links.RouteEntityLink(
            trip_stop_time.trip.route
        )
        trip_stop_time_response["trip"]["last_stop"]["href"] = links.StopEntityLink(
            last_stop
        )
    return trip_stop_time_response


class _TraversalMode(enum.Enum):
    """
    Different ways in which the stop tree can be traversed starting from a
    base node.
    """

    DESCENDANTS = 4
    ALL = 5


def _traverse_stops_tree(
    base, node_function, base_traversal_mode: _TraversalMode, only_visit_stations: bool
):
    """
    This method provides a mechanism for traversing the stops tree.
    There are multiple traversal modes available: currently ALL, which
    traverses the whole tree, and DESCENDANTS, which traverses the descendants
    of the base node.

    The method applies a function to each node in the traversal. It uses a
    depth-first search, so when evaluating the function at a given node
    the results of evaluating the function at the nodes the next level
    deep are available. The return of this function is the value of the node
    function at the base.

    The node function provided must have the following signature:

    def node_function(stop, visited_parent, parent_return, children_return):
        pass

    The arguments passed to the node function are:
    - stop: the current node being evaluated
    - visited_parent: a boolean denoting whether the parent has been traversed
       already. This being False does not mean the parent won't be traversed;
       it means that in the relevant depth first search starting from base,
       the parent node won't be visited before the current node.
    - parent_return: the result of the node_function applied ot the parent.
       If visited_parent is False, this is None.
    - child_returns: a list containing the results of the node_function
       applied to child nodes of this node. If the child nodes were
       not traversed, this will be None.

    :param base: the base node to start at
    :param node_function: the node function
    :param base_traversal_mode: the traversal mode
    :param only_visit_stations: whether to only visit stations
    :return: the result of the node_function at the base
    """

    def visit_node(stop, traversal_mode, previous=None):
        visit_parent = (
            traversal_mode is _TraversalMode.ALL and stop.parent_stop is not None
        )
        visit_children = (
            traversal_mode is _TraversalMode.DESCENDANTS
            or traversal_mode is _TraversalMode.ALL
        )

        if visit_parent:
            parent_traversal_mode = _TraversalMode.ALL
            parent_return = visit_node(
                stop.parent_stop, parent_traversal_mode, previous=stop
            )
        else:
            parent_return = None

        if visit_children:
            children_traversal_mode = _TraversalMode.DESCENDANTS

            children_returns = []
            for child_stop in stop.child_stops:
                if previous is not None and child_stop.pk == previous.pk:
                    continue
                if only_visit_stations and not child_stop.is_station:
                    continue
                children_returns.append(visit_node(child_stop, children_traversal_mode))
        else:
            children_returns = None
        return node_function(stop, visit_parent, parent_return, children_returns)

    return visit_node(base, base_traversal_mode)


def _build_stop_tree_response(
    base, stop_pk_to_service_maps_response, return_links, return_only_stations
):
    """
    Build the stop tree response.

    The response consists of a nested dictionary representing the stop tree
    with the given base as the starting point of the representation. A given
    stop in the dictionary can contain 'parent_stop' and 'child_stops'
    keys which point to relevant related stops in the tree.

    Each stop appearing also contains its short representation, its service
    map representation and, optionally, a link to the stop.

    :param base: the base node for the representation
    :param stop_pk_to_service_maps_response: a map containing the service map
                                             response
    :param return_links: whether to return links
    :param return_only_stations: whether to only return stations
    :return: the dictionary described above.
    """

    def node_function(stop, visited_parent, parent_return, children_return):
        response = {
            **stop.short_repr(),
            "service_maps": stop_pk_to_service_maps_response[stop.pk],
        }
        if return_links:
            response["href"] = links.StopEntityLink(stop)
        if visited_parent:
            response["parent_stop"] = parent_return
        if stop.parent_stop is None:
            response["parent_stop"] = None
        if children_return is not None:
            response["child_stops"] = children_return
        return response

    return _traverse_stops_tree(
        base, node_function, _TraversalMode.ALL, return_only_stations
    )


def _stop_accumulator(stop, is_parent, parent_stops, child_stops_list):
    """
    If the stop tree is traversed with this method, each node returns
    a list containing itself and all of the stops deeper in the traversal.
    Consequently, the result of the complete traversal is the list of all
    stops traversed.
    """
    response = [stop]
    if is_parent:
        response.extend(parent_stops)
    if child_stops_list is not None:
        for child_stop in child_stops_list:
            response.extend(child_stop)
    return response


def _get_stop_descendants(base):
    """
    List all stop descendants of the given base stop.

    The response includes the base.
    """
    return _traverse_stops_tree(
        base, _stop_accumulator, _TraversalMode.DESCENDANTS, False
    )


def _get_all_stations(base):
    """
    Get all stations in the stop tree containing base.
    """
    return _traverse_stops_tree(base, _stop_accumulator, _TraversalMode.ALL, True)


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
        return {rule.name for rule in self._rules}

    def match(self, trip_stop_time):
        """
        Find the direction name associate to the TripStopTime by matching
        the appropriate rule.

        :param trip_stop_time: the TripStopTime
        :return: the direction name
        """
        stop = trip_stop_time.stop
        cache_key = (stop.pk, trip_stop_time.trip.direction_id, trip_stop_time.track)
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
