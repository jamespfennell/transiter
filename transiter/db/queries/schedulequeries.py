import logging
import time
import typing

import sqlalchemy.sql.expression as sql
from sqlalchemy import func

from transiter.db import dbconnection, models

logger = logging.getLogger(__name__)


def get_scheduled_trip_pk_to_path_in_system(system_pk):
    """
    Get a map of trip PK to the path of that trip for every scheduled trip in a system.
    By path is meant a list of stop_pks that the trip stops at. This method completely
    bypasses the ORM and so relatively efficient.

    :param system_pk: the system's PK
    :return: map of trip PK to list of stop PKs
    """
    start_time = time.time()
    session = dbconnection.get_session()
    query = (
        session.query(
            models.ScheduledTripStopTime.trip_pk, models.ScheduledTripStopTime.stop_pk
        )
        .join(
            models.ScheduledTrip,
            models.ScheduledTrip.pk == models.ScheduledTripStopTime.trip_pk,
        )
        .join(
            models.ScheduledService,
            sql.and_(
                models.ScheduledService.pk == models.ScheduledTrip.service_pk,
                models.ScheduledService.system_pk == system_pk,
            ),
        )
        .order_by(
            models.ScheduledTripStopTime.trip_pk,
            models.ScheduledTripStopTime.stop_sequence,
        )
    )
    trip_pk_to_stop_pks = {}
    for trip_pk, stop_pk in query:
        if trip_pk not in trip_pk_to_stop_pks:
            trip_pk_to_stop_pks[trip_pk] = []
        trip_pk_to_stop_pks[trip_pk].append(stop_pk)
    logger.info(
        "Query get_scheduled_trip_pk_to_path_in_system took {:.2} seconds".format(
            time.time() - start_time
        )
    )
    return trip_pk_to_stop_pks


def list_scheduled_trips_with_times_in_system(system_pk):
    """
    List scheduled trips in a system along with their start and end times.

    Start time is the minimum of the trips departure times; end time is the maximum.

    :param system_pk: the system's PK
    :return: list of three tuples (ScheduledTrip, start time, end time)
    """
    start_time = time.time()
    session = dbconnection.get_session()
    first_stop_query = (
        session.query(
            models.ScheduledTripStopTime.trip_pk.label("trip_pk"),
            func.min(models.ScheduledTripStopTime.departure_time).label("time"),
        )
        .group_by(models.ScheduledTripStopTime.trip_pk)
        .subquery()
    )
    last_stop_query = (
        session.query(
            models.ScheduledTripStopTime.trip_pk.label("trip_pk"),
            func.max(models.ScheduledTripStopTime.departure_time).label("time"),
        )
        .group_by(models.ScheduledTripStopTime.trip_pk)
        .subquery()
    )
    query = (
        session.query(
            models.ScheduledTrip, first_stop_query.c.time, last_stop_query.c.time
        )
        .join(
            models.ScheduledService,
            sql.and_(
                models.ScheduledService.pk == models.ScheduledTrip.service_pk,
                models.ScheduledService.system_pk == system_pk,
            ),
        )
        .join(first_stop_query, models.ScheduledTrip.pk == first_stop_query.c.trip_pk)
        .join(last_stop_query, models.ScheduledTrip.pk == last_stop_query.c.trip_pk)
    )
    result = query.all()
    logger.info(
        "Query list_scheduled_trips_with_times_in_system took {:.2} seconds".format(
            time.time() - start_time
        )
    )
    return result


def get_trip_id_to_pk_map_by_feed_pk(feed_pk):
    id_to_pk = {}
    query = (
        dbconnection.get_session()
        .query(models.ScheduledTrip.id, models.ScheduledTrip.pk)
        .filter(
            models.ScheduledService.pk == models.ScheduledTrip.service_pk,
            models.ScheduledService.source_pk == models.FeedUpdate.pk,
            models.FeedUpdate.feed_pk == feed_pk,
        )
    )
    for (id_, pk) in query.all():
        id_to_pk[id_] = pk
    return id_to_pk


def list_trips_by_system_pk_and_trip_ids(
    system_pk, trip_ids
) -> typing.List[models.ScheduledTrip]:
    """

    :param system_pk:
    :param trip_ids:
    :return: list of models.ScheduledTrip
    """

    query = (
        dbconnection.get_session()
        .query(models.ScheduledTrip)
        .filter(
            models.ScheduledTrip.id.in_(trip_ids),
            models.ScheduledService.pk == models.ScheduledTrip.service_pk,
            models.ScheduledService.system_pk == system_pk,
        )
    )
    return query.all()
