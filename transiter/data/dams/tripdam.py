import sqlalchemy
import sqlalchemy.sql.expression as sql
from sqlalchemy.orm import selectinload

from transiter import models
from transiter.data import dbconnection


def list_all_from_feed(feed_pk):
    session = dbconnection.get_session()
    query = (
        session.query(models.Trip)
        .filter(
            models.Trip.source_pk == models.FeedUpdate.pk,
            models.FeedUpdate.feed_pk == feed_pk,
        )
        .options(selectinload(models.Trip.stop_times))
    )
    return query.all()


def list_all_in_route_by_pk(route_pk):
    """
    List all of the Trips in a route.

    :param route_pk: the route's PK
    :return: list of Trips
    """
    session = dbconnection.get_session()
    query = (
        session.query(models.Trip)
        .filter(models.Trip.route_pk == route_pk)
        .options(selectinload(models.Trip.stop_times))
    )
    return query.all()


def get_in_route_by_id(system_id, route_id, trip_id):
    """
    Get a Trip using IDs.

    :param system_id: the system's ID
    :param route_id: the route's ID
    :param trip_id: the trip's ID
    :return: the Trip
    """
    session = dbconnection.get_session()
    return (
        session.query(models.Trip)
        .join(models.Route, models.Route.pk == models.Trip.route_pk)
        .filter(models.Route.system_id == system_id)
        .filter(models.Route.id == route_id)
        .filter(models.Trip.id == trip_id)
        .one_or_none()
    )


def get_trip_pk_to_last_stop_map(trip_pks):
    """
    Get the map to trip PK to the last stop for the trip.

    :param trip_pks: the trip PKs to build the map for
    :return: trip_pk to Stop
    """
    session = dbconnection.get_session()

    sub_query = (
        session.query(
            models.TripStopTime.trip_pk,
            sqlalchemy.func.max(models.TripStopTime.stop_sequence),
        )
        .group_by(models.TripStopTime.trip_pk)
        .filter(models.TripStopTime.trip_pk.in_(trip_pks))
    )
    query = (
        session.query(models.TripStopTime.trip_pk, models.Stop)
        .filter(models.TripStopTime.stop_pk == models.Stop.pk)
        .filter(
            sqlalchemy.tuple_(
                models.TripStopTime.trip_pk, models.TripStopTime.stop_sequence
            ).in_(sub_query)
        )
    )
    trip_pk_to_last_stop = {trip_pk: None for trip_pk in trip_pks}
    for trip_pk, last_stop in query:
        trip_pk_to_last_stop[trip_pk] = last_stop
    return trip_pk_to_last_stop


def get_trip_pk_to_path_map(route_pk):
    """
    Get a map of trip PK to the path of the trip for every trip in a route.

    The path here is a list of stop PKs.

    :param route_pk: the route's PK
    :return: map described above
    """
    statement = (
        sql.select([models.TripStopTime.trip_pk, models.TripStopTime.stop_pk])
        .select_from(sql.join(models.TripStopTime, models.Trip))
        .where(models.Trip.route_pk == route_pk)
        .order_by(models.TripStopTime.trip_pk, models.TripStopTime.stop_sequence)
    )
    session = dbconnection.get_session()
    trip_pk_to_stop_pks = {}
    for trip_pk, stop_pk in session.execute(statement):
        if trip_pk not in trip_pk_to_stop_pks:
            trip_pk_to_stop_pks[trip_pk] = []
        trip_pk_to_stop_pks[trip_pk].append(stop_pk)
    return trip_pk_to_stop_pks
