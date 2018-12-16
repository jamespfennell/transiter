
from transiter.data.dams import routedam
from transiter.data import syncutil, database


def sync_route_statuses(system, route_statuses):
    session = database.get_session()
    existing_statuses = routedam.list_all_route_statuses_in_system(system.id)

    (expired_statuses, __, __) = syncutil.copy_pks(
        existing_statuses, route_statuses, ('id', ))

    for expired_status in expired_statuses:
        session.delete(expired_status)

    route_id_to_route = {route.id: route for route in system.routes}

    for route_status in route_statuses:
        persisted_route_status = session.merge(route_status)
        route_ids = route_status.route_ids
        persisted_route_status.routes = [
            route_id_to_route[route_id] for route_id in route_ids
        ]

