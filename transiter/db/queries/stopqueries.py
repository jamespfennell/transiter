import collections
import typing

from sqlalchemy import sql
from sqlalchemy.orm import joinedload, selectinload, aliased

from transiter.db import dbconnection, models
from transiter.db.queries import genericqueries


def list_all_in_geographical_bounds(
    lower_lat, upper_lat, lower_lon, upper_lon, system_id,
):
    query = (
        dbconnection.get_session()
        .query(models.Stop)
        .filter(models.Stop.parent_stop_pk.is_(None))
        .filter(models.Stop.latitude >= lower_lat)
        .filter(models.Stop.latitude <= upper_lat)
        .filter(models.Stop.longitude >= lower_lon)
        .filter(models.Stop.longitude <= upper_lon)
    )
    if system_id is not None:
        query = query.join(models.System).filter(models.System.id == system_id)
    return query.all()


def list_all_in_system(system_id, stop_ids=None):
    return genericqueries.list_in_system(
        models.Stop, system_id, order_by_field=models.Stop.id, ids=stop_ids
    )


def list_all_transfers_in_system(
    system_id, from_stop_ids=None, to_stop_ids=None
) -> typing.List[models.Transfer]:
    query = (
        dbconnection.get_session()
        .query(models.Transfer)
        .join(models.System)
        .filter(models.System.id == system_id)
        .options(joinedload(models.Transfer.from_stop))
        .options(joinedload(models.Transfer.to_stop))
    )
    if from_stop_ids is not None:
        from_stop = aliased(models.Stop)
        query = query.join(from_stop, models.Transfer.from_stop).filter(
            from_stop.id.in_(from_stop_ids)
        )
    if to_stop_ids is not None:
        query = query.join(models.Stop, models.Transfer.to_stop).filter(
            models.Stop.id.in_(to_stop_ids)
        )
    return list(query.all())


def list_all_transfers_at_stops(from_stop_pks) -> typing.List[models.Transfer]:
    query = (
        dbconnection.get_session()
        .query(models.Transfer)
        .filter(models.Transfer.from_stop_pk.in_(from_stop_pks))
        .options(joinedload(models.Transfer.to_stop))
    )
    return list(query.all())


def get_in_system_by_id(system_id, stop_id):
    return genericqueries.get_in_system_by_id(models.Stop, system_id, stop_id)


def get_id_to_pk_map_in_system(
    system_pk: int, stop_ids: typing.Iterable[str] = None
) -> typing.Dict[str, int]:
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


def build_stop_pk_to_descendant_pks_map(
    stop_pks, stations_only=False
) -> typing.Dict[int, typing.Set[int]]:
    """
    Construct a map whose key is a stop's pk and value is a list of all stop pks
    that are descendents of that stop.
    """
    session = dbconnection.get_session()
    descendant_cte = (
        session.query(
            models.Stop.pk.label("ancestor_pk"), models.Stop.pk.label("descendent_pk")
        )
        .filter(models.Stop.pk.in_(stop_pks))
        .cte(name="descendent_cte", recursive=True)
    )
    recursive_part = session.query(
        descendant_cte.c.ancestor_pk.label("ancestor_pk"),
        models.Stop.pk.label("descendent_pk"),
    ).filter(models.Stop.parent_stop_pk == descendant_cte.c.descendent_pk)
    if stations_only:
        recursive_part = recursive_part.filter(
            models.Stop.type.in_(models.Stop.STATION_TYPES)
        )
    descendant_cte = descendant_cte.union_all(recursive_part)

    stop_pk_to_descendant_pks = collections.defaultdict(set)
    for stop_pk, descendant_pk in session.query(descendant_cte).all():
        stop_pk_to_descendant_pks[stop_pk].add(descendant_pk)
    return dict(stop_pk_to_descendant_pks)


def list_all_stops_in_stop_tree(stop_pk) -> typing.Iterable[models.Stop]:
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
        .filter(
            sql.and_(
                models.Trip.current_stop_sequence >= 0,
                models.Trip.current_stop_sequence <= models.TripStopTime.stop_sequence,
            )
        )  # TODO: test
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
        session.query(models.Stop.pk, models.Stop.parent_stop_pk, models.Stop.type)
        .filter(models.Stop.system_pk == models.System.pk)
        .filter(models.System.id == system_id)
    )
    stop_pk_to_station_pk = {}
    for stop_pk, parent_stop_pk, stop_type in query:
        if stop_type in models.Stop.STATION_TYPES or parent_stop_pk is None:
            stop_pk_to_station_pk[stop_pk] = stop_pk
        else:
            stop_pk_to_station_pk[stop_pk] = parent_stop_pk
    return stop_pk_to_station_pk


def delete_transfers_in_system(system_pk):
    # TODO
    session = dbconnection.get_session()
