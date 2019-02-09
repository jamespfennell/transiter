from transiter.data.dams import routedam, stopdam, tripdam
from transiter.data import database, syncutil
from transiter import models
import warnings

class TripDataCleaner:

    def __init__(self, trip_cleaners, stu_cleaners):
        self._trip_cleaners = trip_cleaners
        self._stu_cleaners = stu_cleaners

    def clean(self, trips):
        trips_to_keep = []
        for trip in trips:
            result = True
            for trip_cleaner in self._trip_cleaners:
                result = trip_cleaner(trip)
                if not result:
                    break
            if not result:
                continue

            for stop_time_update in trip.stop_events:
                for stu_cleaner in self._stu_cleaners:
                    stu_cleaner(stop_time_update)

            trips_to_keep.append(trip)

        return trips_to_keep

import time

def sync_trips(system, route_ids, trips):

    if route_ids is None:
        # TODO: make more efficient, perhaps make the dao method
        # get_id_to_pk_map 2nd arg optional
        route_id_to_pk = {
            route.id: route.pk for route in routedam.list_all_in_system(system.id)
        }
    else:
        route_id_to_pk = routedam.get_id_to_pk_map_in_system(system.id, route_ids)
    route_pk_to_trips_dict = {route_pk: {} for route_pk in route_id_to_pk.values()}
    all_stop_ids = set()
    for trip in trips:
        route_pk = route_id_to_pk.get(trip.route_id, None)
        if route_pk is None:
            continue
        route_pk_to_trips_dict[route_pk][trip.id] = trip
        for stu in trip.stop_events:
            all_stop_ids.add(stu.stop_id)

    stop_id_to_pk = stopdam.get_id_to_pk_map_in_system(system.id, all_stop_ids)
    index = 0
    for route_pk, trips_dict in route_pk_to_trips_dict.items():
        index += 1
        sync_trips_in_route(route_pk, trips_dict.values(), stop_id_to_pk)


# This method essentially performs a session.merge operation
# on the Trips. There are two considerations which require additional logic:
#
# - SQL Alchemy merges by identifying Trips with the same pk. In the GTFS only
#   world there are no (globally unique) pks, only (route specific
#   unique) ids. So we first, for every Trip, have to find
#   the pk corresponding to that trip in the DB, if it exists.
#
# - We want to merge in the StopTimeUpdates as well, but we want to keep
#   historical StopTimeUpdates and mark them as passed. After we merge in a Trip
#   its new StopTimeUpdates will be merged in, via the cascade; we then have
#   to manually put the historical StopTimeUpdates back in.
def sync_trips_in_route(route_pk, trips, stop_id_to_pk):
    for trip in trips:
        for stu in trip.stop_events:
            stu.stop_pk = stop_id_to_pk.get(stu.stop_id, None)

    existing_trips = list(tripdam.list_all_in_route_by_pk(route_pk))
    (old_trips, updated_trip_tuples, new_trips) = syncutil.copy_pks(
        existing_trips, trips, ('id', ))

    session = database.get_session()
    for updated_trip, existing_trip in updated_trip_tuples:

        index = 0
        for existing_stu in existing_trip.stop_events:
            if existing_stu.stop_sequence >= updated_trip.current_stop_sequence:
                break
            existing_stu.future = False
            index += 1
        existing_future_stus = existing_trip.stop_events[index:]

        updated_future_stus = []
        for stu in updated_trip.stop_events:
            if stu.stop_pk is not None:
                updated_future_stus.append(stu)
        (old_stus, updated_stu_tuples, new_stus) = syncutil.copy_pks(
            existing_future_stus, updated_future_stus, ('stop_sequence', ))

        for new_stu in new_stus:
            new_stu.trip_pk = existing_trip.pk
            session.add(new_stu)
            """
            # Because of SQL alchemy bugs and crazy behaviour around relationships,
            # we just create a new STU with no existing trip and write to that.
            if new_stu.stop_pk is None:
                continue
            real_new_stu = models.StopTimeUpdate()
            session.add(real_new_stu)
            real_new_stu.trip_pk = existing_trip.pk
            real_new_stu.stop_sequence = new_stu.stop_sequence
            updated_stu_tuples.append((new_stu, real_new_stu))
            """

        for (updated_stu, existing_stu) in updated_stu_tuples:
            # The following manual code is meant as a speed-up to session.merge
            existing_stu.arrival_time = updated_stu.arrival_time
            existing_stu.departure_time = updated_stu.departure_time
            existing_stu.track = updated_stu.track
            existing_stu.future = True
            existing_stu.last_update_time = updated_stu.last_update_time
            existing_stu.stop_pk = updated_stu.stop_pk

        for old_stu in old_stus:
            #print('Deleting stu ', old_stu)
            session.delete(old_stu)

        existing_trip.route_pk = route_pk
        existing_trip.start_time = updated_trip.start_time
        existing_trip.direction_id = updated_trip.direction_id
        existing_trip.vehicle_id = updated_trip.vehicle_id
        existing_trip.current_status = updated_trip.current_status
        existing_trip.current_stop_sequence = updated_trip.current_stop_sequence

    for old_trip in old_trips:
        #print('Deleting trip with pk={}'.format(old_trip.pk))
        session.delete(old_trip)

    for new_trip in new_trips:
        new_trip.route_pk = route_pk
        session.add(new_trip)
        # NOTE: because of a sql alchemy bug, doing this will emit an error
        # https://github.com/sqlalchemy/sqlalchemy/issues/4491
        for stu in new_trip.stop_events:
            if stu.stop_pk is not None:
                session.add(stu)


