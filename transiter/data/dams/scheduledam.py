import sqlalchemy.sql.expression as sql
from sqlalchemy import func

from transiter import models
from transiter.data import dbconnection


def get_scheduled_trip_pk_to_path_in_system():
    statement = sql.select(
        [models.ScheduledTripStopTime.trip_pk, models.ScheduledTripStopTime.stop_pk]
    ).order_by(
        models.ScheduledTripStopTime.trip_pk, models.ScheduledTripStopTime.stop_sequence
    )
    session = dbconnection.get_session()
    trip_pk_to_stop_pks = {}
    for trip_pk, stop_pk in session.execute(statement):
        if trip_pk not in trip_pk_to_stop_pks:
            trip_pk_to_stop_pks[trip_pk] = []
        trip_pk_to_stop_pks[trip_pk].append(stop_pk)
    return trip_pk_to_stop_pks


def list_scheduled_trips_with_times_in_system():
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
        .join(first_stop_query, models.ScheduledTrip.pk == first_stop_query.c.trip_pk)
        .join(last_stop_query, models.ScheduledTrip.pk == last_stop_query.c.trip_pk)
    )
    for trip, start_time, end_time in query:
        yield trip, start_time, end_time
