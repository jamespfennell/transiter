import typing

from transiter import exceptions
from transiter.db import dbconnection, models
from transiter.db.queries import routequeries, systemqueries
from transiter.services import views, helpers
from transiter.services.servicemap import servicemapmanager


@dbconnection.unit_of_work
def list_all_in_system(
    system_id, alerts_detail: views.AlertsDetail = None
) -> typing.List[views.Route]:
    system = systemqueries.get_by_id(system_id, only_return_active=True)
    if system is None:
        raise exceptions.IdNotFoundError(models.System, system_id=system_id)

    response = []
    routes = list(routequeries.list_in_system(system_id))
    for route in routes:
        route_response = views.Route.from_model(route)
        response.append(route_response)
    helpers.add_alerts_to_views(
        response, routes, alerts_detail or views.AlertsDetail.CAUSE_AND_EFFECT,
    )
    return response


@dbconnection.unit_of_work
def get_in_system_by_id(
    system_id, route_id, alerts_detail: views.AlertsDetail = None
) -> views.RouteLarge:
    route = routequeries.get_in_system_by_id(system_id, route_id)
    if route is None:
        raise exceptions.IdNotFoundError(
            models.Route, system_id=system_id, route_id=route_id
        )

    periodicity = routequeries.calculate_periodicity(route.pk)
    if periodicity is not None:
        periodicity = int(periodicity / 6) / 10
    result = views.RouteLarge.from_model(route, periodicity)
    if route.agency is not None:
        result.agency = views.Agency.from_model(route.agency)
    helpers.add_alerts_to_views(
        [result], [route], alerts_detail or views.AlertsDetail.MESSAGES,
    )
    result.service_maps = servicemapmanager.build_route_service_maps_response(route.pk)
    return result
