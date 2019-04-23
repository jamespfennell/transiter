"""
This updater syncs Alerts in a new feed update with those in the database.
"""
from transiter.data.dams import routedam
from transiter.data import syncutil, database


def sync_alerts(system, alerts):
    """
    Set the alerts for a system.

    :param system: the system
    :param alerts: list of Alert models
    """
    session = database.get_session()
    existing_alerts = routedam.list_all_route_statuses_in_system(system.id)

    (expired_alerts, __, __) = syncutil.copy_pks(existing_alerts, alerts, ('id',))

    for expired_alert in expired_alerts:
        session.delete(expired_alert)

    route_id_to_route = {route.id: route for route in system.routes}

    for alert in alerts:
        persisted_alert = session.merge(alert)
        route_ids = alert.route_ids
        persisted_alert.routes = [
            route_id_to_route[route_id] for route_id in route_ids
        ]

