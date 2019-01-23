from transiter import models
from transiter.models.routestatus import route_status_route
from transiter.data import database
from transiter.data.dams import genericqueries

from sqlalchemy import orm


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
        .join(starting_query, models.Stop.pk == starting_query.c.parent_stop_pk))
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


def list_terminus_data(route_pk):
    """
    List terminus data for a route. A terminus is a stop at which a trip
    corresponding to a given route is currently terminating at. For each such
    stop, this method returns a 4 tuple:
    1 The earliest arrival time of a terminating trip
    2 The latest arrival time of a terminating trip
    3 The number of terminating trips
    4 The stop's pk

    :param route_pk: the route's pk
    :return: list of 4-tuples as described above
    """
    session = database.get_session()
    query = """
    SELECT
        MIN(stop_time_update.arrival_time) as first_arrival_time,
        MAX(stop_time_update.arrival_time) as last_arrival_time,
        COUNT(*) as number_of_trips,
        stop_time_update.stop_pk
    FROM route
    INNER JOIN trip
        ON trip.route_pk = route.pk
    INNER JOIN stop_time_update
        ON stop_time_update.pk = (
            SELECT pk
            FROM stop_time_update
            WHERE trip_pk = trip.pk
            AND future = true
            ORDER BY arrival_time DESC
            LIMIT 1
        )
    WHERE route.pk = :route_pk
    AND trip.current_status != 'SCHEDULED'
    GROUP BY stop_time_update.stop_pk;
    """
    result = session.execute(query, {'route_pk': route_pk})
    for row in result:
        yield row


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


def get_route_statuses(route_pks):
    """

    :param route_pks:
    :return:
    """
    route_pks = tuple(route_pks)
    print(route_pks)
    route_pk_to_status_tuple = {route_pk: ('NONE', None) for route_pk in route_pks}
    session = database.get_session()
    query = """
    SELECT route.pk, route_status.type
    FROM route
    LEFT JOIN route_status_route
        ON route.pk = route_status_route.route_pk
    LEFT JOIN route_status
        ON route_status.pk = route_status_route.route_status_pk
    WHERE ( 
        route_status.pk = (
            SELECT route_status.pk
            FROM route_status_route AS inner_rsr
            INNER JOIN route_status
            ON route_status.pk = inner_rsr.route_status_pk
            WHERE route_status_route.route_pk = inner_rsr.route_pk
            ORDER BY 
                route_status.priority DESC,
                route_status.type ASC
            LIMIT 1
        ) 
        OR 
        route_status.pk IS NULL
    )
    AND EXISTS (
        SELECT 1
        FROM stop_time_update
        INNER JOIN trip
            ON trip.pk = stop_time_update.trip_pk
        WHERE trip.route_pk = route.pk
        LIMIT 1
    )
    AND
        route.pk IN :route_pks;   
    """

    result = session.execute(query, {'route_pks': tuple(route_pks)})

    for row in result:
        print(row)
        if row[1] is None:
            route_pk_to_status_tuple[row[0]] = ('GOOD', None)
        else:
            route_pk_to_status_tuple[row[0]] = ('OTHER', row[1])

    return route_pk_to_status_tuple
