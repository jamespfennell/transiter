from typing import Optional

import sqlalchemy.sql.expression as sql

from transiter import models
from transiter.data import dbconnection
from transiter.data.dams import genericqueries


def list_all_in_system(system_id):
    """
    List all routes in a system.

    :param system_id: the system's ID
    :return: a list of Routes
    """
    return genericqueries.list_all_in_system(models.Route, system_id, models.Route.id)


def get_in_system_by_id(system_id, route_id) -> Optional[models.Route]:
    """
    Get a specific route in a system.

    :param system_id: the system's ID
    :param route_id: the route's ID
    :return: Route, if it exists; None if it does not
    """
    return genericqueries.get_in_system_by_id(models.Route, system_id, route_id)


def get_id_to_pk_map_in_system(system_id, route_ids=None):
    """
    Get a map of route ID to route PK for all routes in a system.

    :param system_id: the system's ID
    :param route_ids: an optional collection that limits the keys in the dict
    :return: map of ID to PK
    """
    return genericqueries.get_id_to_pk_map(models.Route, system_id, route_ids)


def calculate_periodicity(route_pk):
    """
    Calculate the periodicity of a route.

    This is average distance in seconds between the route's trips arriving at
    a stop, averaged over all stops at which the route calls.

    :param route_pk: the route's PK
    :return: a float, representing the periodicity in seconds.=
    """
    session = dbconnection.get_session()

    route_stop_pks_stmt = (
        sql.select([models.Stop.pk])
        .select_from(sql.join(models.Stop, models.TripStopTime).join(models.Trip))
        .where(models.Trip.route_pk == route_pk)
        .where(models.TripStopTime.future)
        .where(models.TripStopTime.arrival_time is not None)
        .distinct()
    )
    stop_data_stmt = (
        sql.select(
            [
                sql.func.extract(
                    "epoch",
                    sql.func.max(models.TripStopTime.arrival_time)
                    - sql.func.min(models.TripStopTime.arrival_time),
                ).label("time_diff"),
                sql.func.count().label("number"),
            ]
        )
        .where(models.TripStopTime.stop_pk.in_(route_stop_pks_stmt))
        .group_by(models.TripStopTime.stop_pk)
        .having(sql.func.count() > 1)
    )
    stop_data_alias = sql.alias(stop_data_stmt)
    final_stmt = sql.select(
        [sql.func.avg(stop_data_alias.c.time_diff / (stop_data_alias.c.number - 1))]
    )
    result = [row for row in session.execute(final_stmt)]
    if len(result) > 0:
        return result[0][0]


def list_route_pks_with_current_service(route_pks):
    """
    Given a collection of route PKs, return the subset that have currently
    active trips.

    :param route_pks: collection of route PKs
    :return: a subset of the input
    """
    session = dbconnection.get_session()
    stmt = sql.select([models.Route.pk]).where(
        sql.and_(
            sql.exists(
                sql.select([1])
                .select_from(sql.join(models.TripStopTime, models.Trip))
                .where(models.Trip.route_pk == models.Route.pk)
                .limit(1)
            ),
            models.Route.pk.in_(route_pks),
        )
    )
    return [route_pk for (route_pk,) in session.execute(stmt)]


def get_route_pk_to_highest_priority_alerts_map(route_pks):
    """
    Get a map mapping route PK to the list of alerts for that route with the
    highest priority. The highest priority if determined on a route-by-route
    basis.

    :param route_pks: list of route PKs
    :return: map of route PK to list of Alerts
    """
    route_pk_to_alerts = {route_pk: [] for route_pk in route_pks}
    session = dbconnection.get_session()
    inner_query = (
        session.query(models.Route.pk, sql.func.max(models.Alert.priority))
        .join(models.alert_route, models.alert_route.c.route_pk == models.Route.pk)
        .join(models.Alert, models.Alert.pk == models.alert_route.c.alert_pk)
        .filter(models.Route.pk.in_(route_pks))
        .group_by(models.Route.pk)
    )
    query = (
        session.query(models.Route.pk, models.Alert)
        .join(models.alert_route, models.alert_route.c.route_pk == models.Route.pk)
        .join(models.Alert, models.Alert.pk == models.alert_route.c.alert_pk)
        .filter(sql.tuple_(models.Route.pk, models.Alert.priority).in_(inner_query))
        .order_by(models.Alert.pk)
    )
    for route_pk, alert in query:
        route_pk_to_alerts[route_pk].append(alert)
    return route_pk_to_alerts
