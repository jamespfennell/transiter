import typing

from transiter import parse


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

    def __init__(
        self,
        trip_cleaners: typing.List[typing.Callable[[parse.Trip], bool]],
        stop_time_cleaners: typing.List[
            typing.Callable[[parse.Trip, parse.TripStopTime], bool]
        ],
    ):
        """
        Initialize a new TripDataCleaner

        :param trip_cleaners: list of Trip cleaning functions
        :param stop_time_cleaners: list of TripStopTime cleaning functions
        """
        self._trip_cleaners = trip_cleaners
        self._stop_time_cleaners = stop_time_cleaners

    def clean(self, trips):
        """
        Clean a collection of trips.

        :param trips: the trips to clean
        :return: the cleaned trips with bad trips removed
        """
        trips_to_keep = []
        for trip in trips:
            if not isinstance(trip, parse.Trip):
                trips_to_keep.append(trip)
                continue
            result = True
            for trip_cleaner in self._trip_cleaners:
                result = trip_cleaner(trip)
                if not result:
                    break
            if not result:
                continue

            for stop_time_update in trip.stop_times:
                for stop_time_cleaner in self._stop_time_cleaners:
                    stop_time_cleaner(trip, stop_time_update)

            trips_to_keep.append(trip)

        return trips_to_keep
