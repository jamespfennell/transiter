import sqlalchemy.sql.expression as sql
from sqlalchemy import func

from transiter import models
from transiter.data import database


def list_groups_and_maps_for_stops_in_route(route_pk):
    session = database.get_session()
    query = (
        session.query(models.ServiceMapGroup, models.ServicePattern)
            .join(
            models.System,
            models.System.pk == models.ServiceMapGroup.system_pk
        )
            .join(
            models.Route,
            models.Route.system_id == models.System.id
        )
            .outerjoin(
            models.ServicePattern,
            sql.and_(
                models.ServicePattern.route_pk == models.Route.pk,
                models.ServicePattern.group_pk == models.ServiceMapGroup.pk
            )
        )
            .filter(models.ServiceMapGroup.use_for_stops_in_route)
            .filter(models.Route.pk == route_pk)
    )
    return [(group, map_) for (group, map_) in query]


def get_stop_pk_to_group_id_to_routes_map(stop_pks):
    # TODO: we should return all service maps, even if they don't have routes for the stop
    # TODO: THIS HAS NOT BEEN DONE!
    # TODO: TEST!!
    session = database.get_session()
    query = (
        session.query(
            models.ServiceMapGroup.id,
            models.ServicePatternVertex.stop_pk,
            models.Route
        )
            .join(
            models.ServicePattern,
            models.ServicePattern.group_pk == models.ServiceMapGroup.pk
        )
            .join(
            models.ServicePatternVertex,
            models.ServicePatternVertex.service_pattern_pk == models.ServicePattern.pk
        )
            .join(
            models.Route,
            models.Route.pk == models.ServicePattern.route_pk
        )
            .filter(models.ServicePatternVertex.stop_pk.in_(stop_pks))
            .filter(models.ServiceMapGroup.use_for_routes_at_stop)
    )
    print(query)
    print(stop_pks)
    response = {stop_pk: {} for stop_pk in stop_pks}
    for group_id, stop_pk, route in query:
        if group_id not in response[stop_pk]:
            response[stop_pk][group_id] = []
        response[stop_pk][group_id].append(route)
    return response


# TODO move this to the trip dam
def get_trip_pk_to_path_map(route_pk):
    statement = (
        sql.select([
            models.StopTimeUpdate.trip_pk,
            models.StopTimeUpdate.stop_pk
        ])
            .select_from(
            sql.join(models.StopTimeUpdate, models.Trip)
        )
            .where(models.Trip.route_pk == route_pk)
            .order_by(models.StopTimeUpdate.trip_pk, models.StopTimeUpdate.stop_sequence)
    )
    session = database.get_session()
    trip_pk_to_stop_pks = {}
    for trip_pk, stop_pk in session.execute(statement):
        if trip_pk not in trip_pk_to_stop_pks:
            trip_pk_to_stop_pks[trip_pk] = []
        trip_pk_to_stop_pks[trip_pk].append(stop_pk)
    return trip_pk_to_stop_pks


# TODO stop_pks_map -> paths
# TODO: in system
def get_scheduled_trip_pk_to_stop_pks_map():
    statement = sql.select(
        [
            models.ScheduledTripStopTime.trip_pk,
            models.ScheduledTripStopTime.stop_pk
        ]
    ).order_by(models.ScheduledTripStopTime.trip_pk, models.ScheduledTripStopTime.stop_sequence)
    session = database.get_session()
    trip_pk_to_stop_pks = {}
    for trip_pk, stop_pk in session.execute(statement):
        if trip_pk not in trip_pk_to_stop_pks:
            trip_pk_to_stop_pks[trip_pk] = []
        trip_pk_to_stop_pks[trip_pk].append(stop_pk)
    return trip_pk_to_stop_pks


def list_scheduled_trips_with_times_in_system():
    session = database.get_session()

    first_stop_query = session.query(
        models.ScheduledTripStopTime.trip_pk.label('trip_pk'),
        func.min(models.ScheduledTripStopTime.departure_time).label('time')
    ).group_by(models.ScheduledTripStopTime.trip_pk).subquery()

    last_stop_query = session.query(
        models.ScheduledTripStopTime.trip_pk.label('trip_pk'),
        func.max(models.ScheduledTripStopTime.departure_time).label('time')
    ).group_by(models.ScheduledTripStopTime.trip_pk).subquery()

    query = (
        session.query(
            models.ScheduledTrip,
            first_stop_query.c.time,
            last_stop_query.c.time,
        )
            .join(
            first_stop_query,
            models.ScheduledTrip.pk == first_stop_query.c.trip_pk
        )
            .join(
            last_stop_query,
            models.ScheduledTrip.pk == last_stop_query.c.trip_pk
        )
    )
    for trip, start_time, end_time in query:
        yield trip, start_time, end_time
