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


def get_id_to_pk_map_in_system(system_id, route_ids):
    return genericqueries.get_id_to_pk_map(
        models.Route, system_id, route_ids
    )


def _expand_to_ancestors(initial_query):
    """
    Given an initial query that queries for models.Stop entities, this
    function returns a CTE that contains the stop entities
    matching the query and all of their ancestors.

    For example:
        query = session.query(models.Stop).filter(models.Stop.id == 'L03N')
        expanded_cte = _expand_to_ancestors(query, session)
        for row in session.query(expanded_cte.c.id):
            print(row)

    This prints L03N, L03, 635-L03-R20

    :param initial_query:
    :return:
    """
    starting_query = initial_query.cte(recursive=True)
    recursion_query = (
        orm.query.Query(models.Stop)
        .join(starting_query, models.Stop.pk == starting_query.c.parent_stop_pk)
    )
    return starting_query.union_all(recursion_query)


def list_active_stop_ids(route_pk):
    """
    List the stop ids at which trips corresponding to the given route are
    currently stopping at
    :param route_pk: the pk of the route
    :return: list of stop ids
    """
    session = database.get_session()

    query = (
        session.query(models.Stop)
        .distinct()
        .join(models.StopTimeUpdate, models.Stop.pk == models.StopTimeUpdate.stop_pk)
        .join(models.Trip, models.Trip.pk == models.StopTimeUpdate.trip_pk)
        .join(models.Route, models.Trip.route_pk == models.Route.pk)
        .filter(models.Route.pk == route_pk)
    )
    expanded_query = session.query(_expand_to_ancestors(query).c.id)
    for row in expanded_query:
        yield row[0]


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
    for row in query:
        yield row


def list_route_statuses(route_pks):
    """

    :param route_pks:
    :return:
    """
    route_pks = tuple(route_pks)
    route_pk_to_status_tuple = {route_pk: 'No service' for route_pk in route_pks}
    session = database.get_session()

    inner_rsr = sql.alias(models.route_status_route)
    inner_statement = (
        sql.select([inner_rsr.c.route_pk, inner_rsr.c.route_status_pk])
        .select_from(sql.join(inner_rsr, models.RouteStatus))
        .where(models.Route.pk == inner_rsr.c.route_pk)
        .order_by(models.RouteStatus.priority.desc(), models.RouteStatus.type)
        .limit(1)
    )
    stmt = (
        sql.select([models.Route.pk, models.RouteStatus.type])
        .select_from(
            sql.join(
                sql.join(
                    models.Route,
                    models.route_status_route,
                    sql.tuple_(
                        models.route_status_route.c.route_pk,
                        models.route_status_route.c.route_status_pk
                    ) == inner_statement,
                    isouter=True
                ),
                models.RouteStatus,
                isouter=True
            )
        )
        .where(
            sql.exists(
                sql.select([1])
                .select_from(sql.join(models.StopTimeUpdate, models.Trip))
                .where(models.Trip.route_pk == models.Route.pk)
                .limit(1)
            )
        )
        .where(models.Route.pk.in_(route_pks))
    )
    for row in session.execute(stmt):
        if row[1] is None:
            route_pk_to_status_tuple[row[0]] = 'Good service'
        else:
            route_pk_to_status_tuple[row[0]] = row[1]

    return route_pk_to_status_tuple
