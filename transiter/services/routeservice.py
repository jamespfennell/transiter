"""
The route service is used to retrieve data about routes.
"""

import enum

from transiter.data import database
from transiter.data.dams import routedam, systemdam
from transiter.general import linksutil, exceptions
from transiter.models import RouteStatus

# TODO: docs
# TODO: tests (100% code coverage for this class)
# TODO: good time to rename RouteStatus -> Alert?


@database.unit_of_work
def list_all_in_system(system_id, show_links=False):
    """
    Get representations for all routes in a system.
    :param system_id: the text id of the system
    :return: a list of short model.Route representations with an additional
    'service_status' entry describing the current status.

    .. code-block:: json

        [
            {
                <fields in a short model.Route representation>,
                'service_status': <service status>
            },
            ...
        ]

    """
    system = systemdam.get_by_id(system_id)
    if system is None:
        raise exceptions.IdNotFoundError
    response = []
    routes = list(routedam.list_all_in_system(system_id))
    route_pk_to_status = (
        _construct_route_pk_to_status_map(route.pk for route in routes)
    )
    for route in routes:
        route_response = {
            **route.short_repr(),
            'status': route_pk_to_status[route.pk]
        }
        if show_links:
            route_response['href'] = linksutil.RouteEntityLink(route)
        response.append(route_response)
    return response


@database.unit_of_work
def get_in_system_by_id(system_id, route_id, show_links=False):
    """
    Get a representation for a route in the system
    :param system_id: the system's text id
    :param route_id: the route's text id
    :return:
    """
    route = routedam.get_in_system_by_id(system_id, route_id)
    if route is None:
        raise exceptions.IdNotFoundError
    status = _construct_route_status(route.pk)
    frequency = routedam.calculate_frequency(route.pk)
    if frequency is not None:
        frequency = int(frequency/6)/10
    response = {
        **route.long_repr(),
        'frequency': frequency,
        'status': status,
        'alerts':
            [alert.short_repr() for alert in route.route_statuses],
        'service_maps': []
    }

    # TODO: also return empty service maps? Yes, don't rely on the DB.
    # Need a new DAM method list_service_maps_in_route
    for service_map in route.service_patterns:
        if not service_map.group.use_for_stops_in_route:
            continue
        service_map_response = {
            'group_id': service_map.group.id,
            'stops': []
        }
        for entry in service_map.vertices:
            stop_response = entry.stop.short_repr()
            if show_links:
                stop_response.update({
                    'href': linksutil.StopEntityLink(entry.stop)
                })
            service_map_response['stops'].append(stop_response)
        response['service_maps'].append(service_map_response)

    return response


class Status(str, enum.Enum):
    NO_SERVICE = 'NO_SERVICE'
    GOOD_SERVICE = 'GOOD_SERVICE'
    PLANNED_SERVICE_CHANGE = 'PLANNED_SERVICE_CHANGE'
    UNPLANNED_SERVICE_CHANGE = 'UNPLANNED_SERVICE_CHANGE'
    DELAYS = 'DELAYS'


def _construct_route_status(route_pk):
    return _construct_route_pk_to_status_map([route_pk])[route_pk]


def _construct_route_pk_to_status_map(route_pks):
    route_pks = set(route_pks)
    route_pk_to_status = {route_pk: Status.NO_SERVICE for route_pk in route_pks}

    route_pk_to_alerts = (
        routedam.get_route_pk_to_highest_priority_alerts_map(route_pks)
    )
    for route_pk, alerts in route_pk_to_alerts.items():
        if len(alerts) == 0:
            continue
        causes = set(alert.cause for alert in alerts)
        effects = set(alert.effect for alert in alerts)
        if RouteStatus.Effect.SIGNIFICANT_DELAYS in effects:
            route_pk_to_status[route_pk] = Status.DELAYS
        elif RouteStatus.Cause.ACCIDENT in causes:
            route_pk_to_status[route_pk] = Status.UNPLANNED_SERVICE_CHANGE
        else:
            route_pk_to_status[route_pk] = Status.PLANNED_SERVICE_CHANGE
        route_pks.remove(route_pk)

    for route_pk in routedam.list_route_pks_with_current_service(route_pks):
        route_pk_to_status[route_pk] = Status.GOOD_SERVICE

    return route_pk_to_status

