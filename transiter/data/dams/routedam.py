from transiter import models
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


def list_active_stop_ids(route_pk):
    """
    List the stop ids at which trips corresponding to the given route are
    currently stopping at
    :param route_pk: the pk of the route
    :return: list of stop ids
    """


    session = database.get_session()

    initial_query = (
        session.query(
            models.Stop.pk, models.Stop.parent_stop_pk)
        .filter(models.Stop.id == 'L03N')
        .cte(recursive=True))
    recursion_query = (
        session.query(models.Stop.pk, models.Stop.parent_stop_pk)
        .join(initial_query, models.Stop.pk == initial_query.c.parent_stop_pk))

    final_query = initial_query.union_all(recursion_query)

    print(type(final_query.c))
    q = (
        session.query(models.Stop.id)
        .join(final_query, models.Stop.pk == final_query.c.pk)
    )
    print(q)
    for row in q.all():
        print(row)


    query = (
        session.query(models.Stop.id)
        .distinct()
        .join(models.StopTimeUpdate, models.Stop.pk == models.StopTimeUpdate.stop_pk)
        .join(models.Trip, models.Trip.pk == models.StopTimeUpdate.trip_pk)
        .join(models.Route, models.Trip.route_pk == models.Route.pk)
        .filter(models.Route.pk == route_pk)
    )
    for row in query:
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
