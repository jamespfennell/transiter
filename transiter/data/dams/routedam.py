import sqlalchemy.orm as orm
import sqlalchemy.sql.expression as sql

from transiter import models
from transiter.data import database
from transiter.data.dams import genericqueries


def list_all_in_system(system_id):
    yield from genericqueries.list_all_in_system(
        models.Route, system_id, models.Route.id
    )


def get_in_system_by_id(system_id, route_id):
    return genericqueries.get_in_system_by_id(
        models.Route, system_id, route_id
    )


def get_id_to_pk_map_in_system(system_id, route_ids=None):
    return genericqueries.get_id_to_pk_map(
        models.Route, system_id, route_ids
    )




def calculate_frequency(route_pk):
    session = database.get_session()

    route_stop_pks_stmt = (
        sql.select([models.Stop.pk])
        .select_from(
            sql.join(models.Stop, models.StopTimeUpdate).join(models.Trip)
        )
        .where(models.Trip.route_pk == route_pk)
        .where(models.Trip.current_status != 'SCHEDULED')
        .where(models.StopTimeUpdate.future)
        .where(models.StopTimeUpdate.arrival_time != None)
        .distinct()
    )
    stop_data_stmt = (
        sql.select([
            sql.func.extract(
                'epoch',
                sql.func.max(models.StopTimeUpdate.arrival_time) -
                sql.func.min(models.StopTimeUpdate.arrival_time)
            ).label('time_diff'),
            sql.func.count().label('number')]
        )
        .where(models.StopTimeUpdate.stop_pk.in_(route_stop_pks_stmt))
        .group_by(models.StopTimeUpdate.stop_pk)
        .having(sql.func.count() > 1)
    )
    stop_data_alias = sql.alias(stop_data_stmt)
    final_stmt = (
        sql.select([
            sql.func.avg(stop_data_alias.c.time_diff / (stop_data_alias.c.number - 1))])
    )
    for row in session.execute(final_stmt):
        return row[0]
    return None


def list_all_route_statuses_in_system(system_id):
    session = database.get_session()
    query = (
        session.query(models.RouteStatus)
        .join(models.Route, models.RouteStatus.routes)
        .join(models.System)
        .filter(models.System.id == system_id)
    )
    l = []
    for row in query:
        l.append(row)
    return l


def list_route_pks_with_current_service(route_pks):
    session = database.get_session()
    stmt = (
        sql.select([models.Route.pk])
        .where(
            sql.and_(
                sql.exists(
                    sql.select([1])
                    .select_from(sql.join(models.StopTimeUpdate, models.Trip))
                    .where(models.Trip.route_pk == models.Route.pk)
                    .limit(1)
                ),
                models.Route.pk.in_(route_pks)
            )
        )
    )
    return [route_pk for (route_pk, ) in session.execute(stmt)]


def get_route_pk_to_highest_priority_alerts_map(route_pks):
    route_pk_to_alerts = {route_pk: [] for route_pk in route_pks}
    session = database.get_session()
    inner_query = (
        session.query(
            models.Route.pk,
            sql.func.max(models.RouteStatus.priority)
        )
        .join(models.route_status_route)
        .join(models.RouteStatus)
        .filter(models.Route.pk.in_(route_pks))
        .group_by(models.Route.pk)
    )
    query = (
        session.query(models.Route.pk, models.RouteStatus)
        .join(models.route_status_route)
        .join(models.RouteStatus)
        .filter(
            sql.tuple_(
                models.Route.pk,
                models.RouteStatus.priority
            ).in_(
                inner_query
            )
        )
    )
    for route_pk, alert in query:
        route_pk_to_alerts[route_pk].append(alert)
    return route_pk_to_alerts
