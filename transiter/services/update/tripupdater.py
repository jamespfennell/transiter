"""
The trip updater is used to synchronize Trips constructed from data feeds
such as GTFS Realtime with Trips in the database. It also contains a Trip
cleaning utility.
"""
from transiter import models
from transiter.data import dbconnection
from transiter.data.dams import stopdam, tripdam
from transiter.services.servicemap import servicemapmanager


class TripDataCleaner:
    """
    The TripDataCleaner provides a mechanism for cleaning valid and removing
    invalid Trips and TripStopTimes.

    To use the TripDataCleaner, you must provide a number of cleaning functions.
    Trip cleaning functions accept two arguments - the current FeedUpdate
    and the Trip being cleaned,
    and perform some operations to clean up the trip - for example, switching
    the direction of Trips in a given route to compensate for a known bug in a
    Transit agency's data feed. If the cleaner returns
    False, then that Trip is removed from the collection. TripStopTime cleaners
    work identically.

    After initializing the cleaner with cleaning functions, a list of Trips
    is passed into its clean method. The cleaners operate on all of the Trips
    and their contained TripStopTimes, remove entities based on cleaner function
    results, and returns the list of cleaned trips.
    """

    def __init__(self, trip_cleaners, stop_time_cleaners):
        """
        Initialize a new TripDataCleaner

        :param trip_cleaners: list of Trip cleaning functions
        :param stop_time_cleaners: list of TripStopTime cleaning functions
        """
        self._trip_cleaners = trip_cleaners
        self._stop_time_cleaners = stop_time_cleaners

    def clean(self, feed_update, trips):
        """
        Clean a collection of trips.

        :param feed_update: the feed update
        :param trips: the trips to clean
        :return: the cleaned trips with bad trips removed
        """
        trips_to_keep = []
        for trip in trips:
            result = True
            for trip_cleaner in self._trip_cleaners:
                result = trip_cleaner(feed_update, trip)
                if not result:
                    break
            if not result:
                continue

            for stop_time_update in trip.stop_times:
                for stop_time_cleaner in self._stop_time_cleaners:
                    stop_time_cleaner(feed_update, stop_time_update)

            trips_to_keep.append(trip)

        return trips_to_keep


def sync_trips(system, trips, route_ids=None):
    """
    Synchronize the trips in xa given set of routes within a system.

    Before merging the feed trips into the database, two pre-processing actions occur:

    (1) TripStopTimes with invalid stop_ids are removed from the trip.

    (2) For Trips that already exist in the database, the TripStopTimes from the past
        are not deleted but instead marked as past. A TripStopTime is deemed to
        be in the past if its stop_sequence is less that the stop_sequence of the
        first TripStopTime in the feed trip.

    :param system: the system
    :param trips: list of Trips
    :param route_ids: list of route IDs for the trips
    """

    if route_ids is None:
        route_id_to_route = {route.id: route for route in system.routes}
    else:
        route_id_to_route = {
            route.id: route for route in system.routes if route.id in route_ids
        }
    route_id_to_trips = {route_id: [] for route_id in route_id_to_route}

    all_stop_ids = set()
    for trip in trips:
        if trip.route_id not in route_id_to_route:
            continue
        route_id_to_trips[trip.route_id].append(trip)
        all_stop_ids.update(stop_time.stop_id for stop_time in trip.stop_times)
    stop_id_to_pk = stopdam.get_id_to_pk_map_in_system(system.id, all_stop_ids)

    for route_id, route_trips in route_id_to_trips.items():
        route = route_id_to_route[route_id]
        trip_maps_changed = _sync_trips_in_route(route, route_trips, stop_id_to_pk)
        if trip_maps_changed:
            servicemapmanager.calculate_realtime_service_map_for_route(route)


def _sync_trips_in_route(route, feed_trips, stop_id_to_pk):
    """
    Synchronize the trips in a route given in a feed for with those in the database.

    The method additionally calculates whether the set of trip maps has
    changed because of the merge.

    :param route: the persisted Route
    :param feed_trips: a list of un-persisted Trips
    :param stop_id_to_pk: a map from stop_id to stop_pk for stop_ids that are
            deemed valid
    :return: boolean, whether the set of trip maps has changed.
    """
    feed_route = models.Route(pk=route.pk)
    feed_route.trips = []

    trip_id_to_trip = {
        trip.id: trip for trip in tripdam.list_all_in_route_by_pk(route.pk)
    }
    existing_trip_maps = set(
        tuple(stop_time.stop_pk for stop_time in trip.stop_times)
        for trip in trip_id_to_trip.values()
    )
    feed_trip_maps = set()

    for feed_trip in feed_trips:
        if len(feed_trip.stop_times) == 0:
            continue

        # Used to ensure that duplicate stops are not put into the DB. This is a
        # safety measure until #36 is resolved.
        future_stop_pks = set()
        for future_stop_time in feed_trip.stop_times:
            stop_pk = stop_id_to_pk.get(future_stop_time.stop_id, None)
            if stop_pk is not None:
                future_stop_pks.add(stop_pk)

        first_future_stop_sequence = feed_trip.stop_times[0].stop_sequence
        feed_stop_times = []
        trip = trip_id_to_trip.get(feed_trip.id, None)
        stop_sequence_to_stop_time_pk = {}
        if trip is not None:
            feed_trip.pk = trip.pk
            for stop_time in trip.stop_times:
                stop_sequence_to_stop_time_pk[stop_time.stop_sequence] = stop_time.pk
            # Prepend the trip by all stop times that have a lower stop_sequence
            # and do not contain any stops that are also in the future. This is a
            # safety measure until #36 is resolved.
            for stop_time in trip.stop_times:
                if stop_time.stop_sequence >= first_future_stop_sequence:
                    break
                if stop_time.stop_pk in future_stop_pks:
                    break
                feed_stop_times.append(
                    models.TripStopTime(
                        pk=stop_time.pk,
                        stop_pk=stop_time.stop_pk,
                        future=False,
                        stop_sequence=stop_time.stop_sequence,
                    )
                )
                del stop_sequence_to_stop_time_pk[stop_time.stop_sequence]

        for feed_stop_time in feed_trip.stop_times:
            stop_pk = stop_id_to_pk.get(feed_stop_time.stop_id, None)
            if stop_pk is None:
                continue
            feed_stop_time.stop_pk = stop_pk
            stop_time_pk = stop_sequence_to_stop_time_pk.get(
                feed_stop_time.stop_sequence, None
            )
            if stop_time_pk is not None:
                del stop_sequence_to_stop_time_pk[feed_stop_time.stop_sequence]
            if stop_time_pk is not None:
                feed_stop_time.pk = stop_time_pk

            feed_stop_times.append(feed_stop_time)

        feed_trip.stop_times = feed_stop_times
        feed_route.trips.append(feed_trip)
        feed_trip_maps.add(
            tuple(stop_time.stop_pk for stop_time in feed_trip.stop_times)
        )

    session = dbconnection.get_session()
    session.merge(feed_route)
    return len(existing_trip_maps ^ feed_trip_maps) != 0
