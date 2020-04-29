"""
The route service is used to retrieve data about routes.
"""
import typing

from transiter import exceptions, models
from transiter.data import dbconnection
from transiter.data.dams import routedam, systemdam
from transiter.models import Alert
from transiter.services import views
from transiter.services.servicemap import servicemapmanager


@dbconnection.unit_of_work
def list_all_in_system(system_id) -> typing.List[views.Route]:
    """
    Get data on all routes in a system.
    """
    system = systemdam.get_by_id(system_id, only_return_active=True)
    if system is None:
        raise exceptions.IdNotFoundError(models.System, system_id=system_id)
    response = []
    routes = list(routedam.list_all_in_system(system_id))
    route_pk_to_status = _construct_route_pk_to_status_map(route.pk for route in routes)
    for route in routes:
        route_response = views.Route.from_model(route)
        route_response.status = route_pk_to_status[route.pk]
        response.append(route_response)
    return response


@dbconnection.unit_of_work
def get_in_system_by_id(system_id, route_id) -> views.RouteLarge:
    """
    Get data for a specific route in a specific system.
    """
    route = routedam.get_in_system_by_id(system_id, route_id)
    if route is None:
        raise exceptions.IdNotFoundError(
            models.Route, system_id=system_id, route_id=route_id
        )
    periodicity = routedam.calculate_periodicity(route.pk)
    if periodicity is not None:
        periodicity = int(periodicity / 6) / 10
    return views.RouteLarge.from_model(
        route,
        _construct_route_status(route.pk),
        periodicity,
        list(map(views.AlertLarge.from_model, route.route_statuses)),
        servicemapmanager.build_route_service_maps_response(route.pk),
    )


Status = views.Route.Status


def _construct_route_status(route_pk):
    """
    Construct the status for a specific route.

    See _construct_route_pk_to_status_map for documentation on how this is
    constructed.
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
