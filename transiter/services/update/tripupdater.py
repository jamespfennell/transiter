from transiter.data.dams import routedam, stopdam, tripdam
from transiter.data import database, syncutil


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
    for route_pk, trips_dict in route_pk_to_trips_dict.items():
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
    print('Number of trips in route: {}'.format(len(trips)))
    for trip in trips:
        trip.route_pk = route_pk
        valid_stus = []
        for stu in trip.stop_events:
            stu.stop_pk = stop_id_to_pk.get(stu.stop_id, None)
            if stu.stop_pk is not None:
                valid_stus.append(stu)
        trip.stop_events = valid_stus

    existing_trips = tripdam.list_all_in_route_by_pk(route_pk)
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

        updated_future_stus = updated_trip.stop_events
        (old_stus, updated_stu_tuples, new_stus) = syncutil.copy_pks(
            existing_future_stus, updated_future_stus, ('stop_sequence', ))

        for new_stu in new_stus:
            new_stu.trip = existing_trip
            session.add(new_stu)

        for (updated_stu, __) in updated_stu_tuples:
            session.merge(updated_stu)

        for old_stu in old_stus:
            session.delete(old_stu)

        session.merge(updated_trip)

    for old_trip in old_trips:
        session.delete(old_trip)

    for new_trip in new_trips:
        session.add(new_trip)


