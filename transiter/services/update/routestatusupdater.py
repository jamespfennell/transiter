
from transiter.data.dams import routedam
from transiter.data import syncutil, database


def sync_route_statuses(system, route_statuses):
    session = database.get_session()
    existing_statuses = list(routedam.list_all_route_statuses_in_system(system.id))
    for s in existing_statuses:
        print(s.pk, s.id)

    (expired_statuses, __, __) = syncutil.copy_pks(
        existing_statuses, route_statuses, ('id', ))

    for s in route_statuses:
        print(s.pk, s.id)
    print('deletingold')
    for expired_status in expired_statuses:
        print(s.pk, s.id)
        session.delete(expired_status)

    route_id_to_route = {route.id: route for route in system.routes}

    for route_status in route_statuses:
        persisted_route_status = session.merge(route_status)
        route_ids = route_status.route_ids
        persisted_route_status.routes = [
            route_id_to_route[route_id] for route_id in route_ids
        ]

