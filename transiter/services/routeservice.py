"""
The route service is used to retrieve data about routes.
"""

import enum

from transiter.data import dbconnection
from transiter.data.dams import routedam, systemdam, servicemapdam
from transiter import exceptions
from transiter.services import links
from transiter.models import Alert


@dbconnection.unit_of_work
def list_all_in_system(system_id, return_links=True):
    """
    Get data on all routes in a system.

    This function returns a list of dictionaries, one dictionary for each
    route. The dictionary for a specific route contains
     * the route's short representation,
     * its status under key 'status',
     * and optionally a link to the route.

    :param system_id: the ID of the system
    :type system_id: str
    :param return_links: whether to return links
    :type return_links: bool
    :return: the list described above
    :rtype: list
    """
    system = systemdam.get_by_id(system_id)
    if system is None:
        raise exceptions.IdNotFoundError
    response = []
    routes = list(routedam.list_all_in_system(system_id))
    route_pk_to_status = _construct_route_pk_to_status_map(route.pk for route in routes)
    for route in routes:
        route_response = {**route.short_repr(), "status": route_pk_to_status[route.pk]}
        if return_links:
            route_response["href"] = links.RouteEntityLink(route)
        response.append(route_response)
    return response


@dbconnection.unit_of_work
def get_in_system_by_id(system_id, route_id, return_links=True):
    """
    Get data for a specific route in a specific system.

    This function returns a dictionary containing,
     * the route's long representation,
     * its status under key 'status',
     * its periodicity under key 'periodicity',
     * its alerts under key 'alerts',
     * all of its service maps for whose group use_for_stops_in_route is true,
       under key 'service_maps',
     * and optionally a link to the route.

    :param system_id: the system ID
    :type system_id: str
    :param route_id: the route ID
    :type route_id: str
    :param return_links: whether to return links
    :type return_links: bool
    :return: the dictionary described above
    :rtype: dict
    """
    route = routedam.get_in_system_by_id(system_id, route_id)
    if route is None:
        raise exceptions.IdNotFoundError
    status = _construct_route_status(route.pk)
    periodicity = routedam.calculate_periodicity(route.pk)
    if periodicity is not None:
        periodicity = int(periodicity / 6) / 10
    response = {
        **route.long_repr(),
        "periodicity": periodicity,
        "status": status,
        "alerts": [alert.long_repr() for alert in route.route_statuses],
        "service_maps": [],
    }

    for group, service_map in servicemapdam.list_groups_and_maps_for_stops_in_route(
        route.pk
    ):
        service_map_response = {"group_id": group.id, "stops": []}
        if service_map is not None:
            for entry in service_map.vertices:
                stop_response = entry.stop.short_repr()
                if return_links:
                    stop_response["href"] = links.StopEntityLink(entry.stop)
                service_map_response["stops"].append(stop_response)
        response["service_maps"].append(service_map_response)

    return response


class Status(str, enum.Enum):
    """Enum containing the possible statuses for a route."""

    NO_SERVICE = "NO_SERVICE"
    GOOD_SERVICE = "GOOD_SERVICE"
    PLANNED_SERVICE_CHANGE = "PLANNED_SERVICE_CHANGE"
    UNPLANNED_SERVICE_CHANGE = "UNPLANNED_SERVICE_CHANGE"
    DELAYS = "DELAYS"


def _construct_route_status(route_pk):
    """
    Construct the status for a specific route.

    See _construct_route_pk_to_status_map for documentation on how this is
    constructed.

    :param route_pk: the route's PK
    :type route_pk: int
    :return: the route's status
    :rtype: Status
    """
    return _construct_route_pk_to_status_map([route_pk])[route_pk]


def _construct_route_pk_to_status_map(route_pks_iter):
    """
    Construct the statuses for multiple routes.

    The algorithm constructs the status by first examining the highest priority
    alerts for a specific route. If there are alerts then,
     * If one of these alerts has the effect SIGNIFICANT_DELAYs, then the status
       of the route is DELAYS.
     * Otherwise, if one of the alerts has planned false, then the status is
       UNPLANNED_SERVICE_CHANGE.
     * Otherwise, the status is PLANNED_SERVICE_CHANGE.

    If there are now no alerts then it is checked to see if there are active
    trips for this route.
     * If so, the status is GOOD_SERVICE.
     * Otherwise, the status is NO_SERVICE.

    :param route_pks_iter: iterator of the routes's PKs
    :type route_pks_iter: iter
    :return: list of TripStatus objects
    :rtype: list
    """
    route_pks = {route_pk for route_pk in route_pks_iter}

    route_pk_to_alerts = routedam.get_route_pk_to_highest_priority_alerts_map(route_pks)

    route_pk_to_status = {route_pk: Status.NO_SERVICE for route_pk in route_pks}
    for route_pk, alerts in route_pk_to_alerts.items():
        if len(alerts) == 0:
            continue
        causes = set(alert.cause for alert in alerts)
        effects = set(alert.effect for alert in alerts)
        if Alert.Effect.SIGNIFICANT_DELAYS in effects:
            route_pk_to_status[route_pk] = Status.DELAYS
        elif Alert.Cause.ACCIDENT in causes:
            route_pk_to_status[route_pk] = Status.UNPLANNED_SERVICE_CHANGE
        else:
            route_pk_to_status[route_pk] = Status.PLANNED_SERVICE_CHANGE
        route_pks.remove(route_pk)

    for route_pk in routedam.list_route_pks_with_current_service(route_pks):
        route_pk_to_status[route_pk] = Status.GOOD_SERVICE

    return route_pk_to_status
