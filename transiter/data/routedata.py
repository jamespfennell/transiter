from transiter import models
from transiter.data import database, genericmethods


def list_all_in_system(system_id):
    yield from genericmethods.list_all_in_system(
        models.Route, system_id, models.Route.id
    )


def get_in_system_by_id(system_id, route_id):
    return genericmethods.get_in_system_by_id(
        models.Route, system_id, route_id
    )


def get_id_to_pk_map_in_system(system_id, ids):
    return genericmethods.get_id_to_pk_map(
        models.Route, system_id, ids
    )


def list_active_stop_ids(route_pk):
    """
    List the stop ids at which trips corresponding to the given route are
    currently stopping at
    :param route_pk: the pk of the route
    :return: list of stop ids
    """
    session = database.get_session()
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

