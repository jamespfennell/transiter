import sqlalchemy
from sqlalchemy.orm import selectinload

from transiter import models
from transiter.data import database


def list_all_in_route_by_pk(route_pk):
    """
    List all of the Trips in a route.

    :param route_pk: the route's PK
    :return: list of Trips
    """
    session = database.get_session()
    query = (
        session.query(models.Trip)
            .filter(models.Trip.route_pk == route_pk)
            .options(selectinload(models.Trip.stop_events))
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
    session = database.get_session()
    return session.query(models.Trip) \
        .join(models.Route, models.Route.pk == models.Trip.route_pk) \
        .filter(models.Route.system_id == system_id) \
        .filter(models.Route.id == route_id) \
        .filter(models.Trip.id == trip_id) \
        .one_or_none()


def get_trip_pk_to_last_stop_map(trip_pks):
    """
    Get the map to trip PK to the last stop for the trip.

    :param trip_pks: the trip PKs to build the map for
    :return: trip_pk to Stop
    """
    session = database.get_session()

    sub_query = (
        session.query(
            models.StopTimeUpdate.trip_pk,
            sqlalchemy.func.max(models.StopTimeUpdate.stop_sequence)
        )
            .group_by(models.StopTimeUpdate.trip_pk)
            .filter(models.StopTimeUpdate.trip_pk.in_(trip_pks))
    )
    query = (
        session.query(models.StopTimeUpdate.trip_pk, models.Stop)
            .filter(models.StopTimeUpdate.stop_pk == models.Stop.pk)
            .filter(
            sqlalchemy.tuple_(
                models.StopTimeUpdate.trip_pk,
                models.StopTimeUpdate.stop_sequence)
                .in_(sub_query)
        )
    )
    trip_pk_to_last_stop = {trip_pk: None for trip_pk in trip_pks}
    for trip_pk, last_stop in query:
        trip_pk_to_last_stop[trip_pk] = last_stop
    return trip_pk_to_last_stop
