from unittest import mock

from transiter import parse
from transiter.parse import utils


def test_clean_all_good():
    trip_cleaners = [mock.MagicMock() for __ in range(3)]
    for cleaner in trip_cleaners:
        cleaner.return_value = True
    stop_event_cleaners = [mock.MagicMock() for __ in range(3)]
    gtfs_cleaner = utils.TripDataCleaner(trip_cleaners, stop_event_cleaners)

    trip = parse.Trip(
        id="trip",
        route_id="L",
        direction_id=True,
        stop_times=[parse.TripStopTime(stop_id="L03")],
    )

    clean_trips = gtfs_cleaner.clean([trip])

    assert [trip] == clean_trips

    for cleaner in trip_cleaners:
        cleaner.assert_called_once_with(trip)
    for cleaner in stop_event_cleaners:
        cleaner.assert_called_once_with(trip, trip.stop_times[0])


def test_clean_buggy_trip():
    trip_cleaners = [mock.MagicMock() for __ in range(3)]
    for cleaner in trip_cleaners:
        cleaner.return_value = True
    trip_cleaners[1].return_value = False
    stop_event_cleaners = [mock.MagicMock() for __ in range(3)]
    gtfs_cleaner = utils.TripDataCleaner(trip_cleaners, stop_event_cleaners)

    trip = parse.Trip(
        id="trip",
        route_id="L",
        direction_id=True,
        stop_times=[parse.TripStopTime(stop_id="L03")],
    )

    clean_trips = gtfs_cleaner.clean([trip])

    assert [] == clean_trips
    trip_cleaners[0].assert_called_once_with(trip)
    trip_cleaners[1].assert_called_once_with(trip)
    trip_cleaners[2].assert_not_called()
    for cleaner in stop_event_cleaners:
        cleaner.assert_not_called()
