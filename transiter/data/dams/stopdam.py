from typing import Dict, Iterable

from sqlalchemy import sql
from sqlalchemy.orm import joinedload, selectinload

from transiter import models
from transiter.data import dbconnection
from transiter.data.dams import genericqueries


def list_all_in_system(system_id):
    """
    List all stops in a system.

    :param system_id: the system's ID
    :return: a list of Stops
    """
    return genericqueries.list_all_in_system(models.Stop, system_id, models.Stop.id)


def get_in_system_by_id(system_id, stop_id):
    """
    Get a specific stop in a system.

    :param system_id: the system's ID
    :param stop_id: the stop's ID
    :return: Stop, if it exists; None if it does not
    """
    return genericqueries.get_in_system_by_id(models.Stop, system_id, stop_id)


def get_id_to_pk_map_in_system(
    system_pk: int, stop_ids: Iterable[str] = None
) -> Dict[str, int]:
    """
    Get a map of stop ID to stop PK for all stops in a system.
    """
    return genericqueries.get_id_to_pk_map(models.Stop, system_pk, stop_ids)


def list_direction_rules_for_stops(stop_pks):
    """
    List all direction rules for a given collection of stops.
    """
    return (
        dbconnection.get_session()
        .query(models.DirectionRule)
        .filter(models.DirectionRule.stop_pk.in_(stop_pks))
        .all()
    )


def list_all_stops_in_stop_tree(stop_pk) -> Iterable[models.Stop]:
    """
    List all stops in the stop tree of a given stop.
    """
    session = dbconnection.get_session()

    # The first CTE retrieves all stop PKs of ancestors of the root stop.
    ancestor_cte = (
        session.query(models.Stop.pk, models.Stop.parent_stop_pk)
        .filter(models.Stop.pk == stop_pk)
        .cte(name="ancestor", recursive=True)
    )
    ancestor_cte = ancestor_cte.union_all(
        session.query(models.Stop.pk, models.Stop.parent_stop_pk).filter(
            models.Stop.pk == ancestor_cte.c.parent_stop_pk
        )
    )

    # The second CTE then retrieves all descendents of all stops from the first CTE.
    # Because the first CTE returns the root of the stops tree, the second CTE returns
    # all stops in the tree.
    relation_cte = (
        session.query(models.Stop.pk, models.Stop.parent_stop_pk)
        .filter(models.Stop.pk == ancestor_cte.c.pk)
        .cte(name="relation", recursive=True)
    )
    relation_cte = relation_cte.union_all(
        session.query(models.Stop.pk, models.Stop.parent_stop_pk).filter(
            models.Stop.parent_stop_pk == relation_cte.c.pk
        )
    )
    query = session.query(models.Stop).filter(models.Stop.pk == relation_cte.c.pk)
    return query.all()


def list_stop_time_updates_at_stops(stop_pks, earliest_time=None, latest_time=None):
    """
    List the future TripStopTimes for a collection of stops.

    The list is ordered by departure time and, in the case of ties, by
    the arrival time.

    Note the Trip and Route objects are eagerly loaded.
    """
    session = dbconnection.get_session()
    query = (
        session.query(models.TripStopTime)
        .filter(models.TripStopTime.stop_pk.in_(stop_pks))
        .filter(models.TripStopTime.trip_pk == models.Trip.pk)
        .filter(models.TripStopTime.future)
        .order_by(models.TripStopTime.departure_time)
        .order_by(models.TripStopTime.arrival_time)
        .options(joinedload(models.TripStopTime.trip))
        .options(selectinload(models.TripStopTime.trip, models.Trip.route))
    )

    if earliest_time is not None:
        earliest_datetime = earliest_time
        query = query.filter(
            sql.or_(
                models.TripStopTime.departure_time >= earliest_datetime,
                models.TripStopTime.arrival_time >= earliest_datetime,
            )
        )
    if latest_time is not None:
        latest_datetime = latest_time
        query = query.filter(
            sql.or_(
                models.TripStopTime.departure_time <= latest_datetime,
                models.TripStopTime.arrival_time <= latest_datetime,
            )
        )
    return query.all()


def get_stop_pk_to_station_pk_map_in_system(system_id):
    """
    Get the map of stop PK to station PK for every stop in a system.

    Right now this method assumes that a stop's station is either itself
    or its parent.

    :param system_id: the system ID
    :return: map of stop PK to stop PK
    """
    session = dbconnection.get_session()
    query = (
        session.query(
            models.Stop.pk, models.Stop.parent_stop_pk, models.Stop.is_station
        )
        .filter(models.Stop.system_pk == models.System.pk)
        .filter(models.System.id == system_id)
    )
    stop_pk_to_station_pk = {}
    for stop_pk, parent_stop_pk, is_station in query:
        if is_station or parent_stop_pk is None:
            stop_pk_to_station_pk[stop_pk] = stop_pk
        else:
            stop_pk_to_station_pk[stop_pk] = parent_stop_pk
    return stop_pk_to_station_pk
