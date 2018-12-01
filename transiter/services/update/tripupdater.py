

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


def sync_trips(route_ids, trips):
    pass
