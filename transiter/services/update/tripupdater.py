from transiter.database.daos import route_dao, stop_dao, trip_dao
from transiter.database import syncutil


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

    route_id_to_pk = route_dao.get_id_to_pk_map(system.id, route_ids)
    print(route_id_to_pk)
    print(route_ids)
    print('# trips: {}'.format(len(trips)))
    route_pk_to_trips_dict = {route_pk: {} for route_pk in route_id_to_pk.values()}
    all_stop_ids = set()
    for trip in trips:
        route_pk = route_id_to_pk.get(trip.route_id, None)
        if route_pk is None:
            continue
        route_pk_to_trips_dict[route_pk][trip.id] = trip
        for stu in trip.stop_events:
            all_stop_ids.add(stu.stop_id)

    stop_id_to_pk = stop_dao.get_id_to_pk_map(system.id, all_stop_ids)
    for route_pk, trips_dict in route_pk_to_trips_dict.items():
        sync_trips_in_route(route_pk, trips_dict.values(), stop_id_to_pk)


def sync_trips_in_route(route_pk, trips, stop_id_to_pk):
    print('Number of trips in route: {}'.format(len(trips)))
    for trip in trips:
        trip.route_pk = route_pk
        for stu in trip.stop_events:
            stu.stop_pk = stop_id_to_pk[stu.stop_id]

    existing_trips = trip_dao.list_all_in_route_by_pk(route_pk)
    (new_trips, updated_trip_tuples, old_trips) = syncutil.copy_pks(
        existing_trips, trips, ('id', ))

    for updated_trip, existing_trip in updated_trip_tuples:


        historical_stus = existing_trip.stop_events[:updated_trip.current_stop_sequence]
        for historical_stu in historical_stus:
            if historical_stu.future:
                historical_stu.future = False

        existing_stus = existing_trip.stop_events[updated_trip.current_stop_sequence:]
        (new_stus, __, __) = syncutil.copy_pks(
            existing_stus,
            updated_trip.stop_events,
            ('stop_sequence', ))
        for new_stu in new_stus:
            new_stu.trip = updated_trip


        updated_trip.stop_events.extend(historical_stus)

    for old_trip in old_trips:
        old_trip.route_pk = None

    # TODO: don't get the session from the dao, get from the database
    session = route_dao.get_session()
    #for new_trip in new_trips:
    #    session.add(new_trip)
    for updated_trip in trips:
        session.merge(updated_trip)

