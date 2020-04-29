import typing

from transiter import exceptions, models
from transiter.data import dbconnection
from transiter.data.dams import tripdam, routedam
from transiter.services import views


@dbconnection.unit_of_work
def list_all_in_route(system_id, route_id) -> typing.List[views.Trip]:
    """
    Get representations for all trips in a system.
    """
    route = routedam.get_in_system_by_id(system_id, route_id)
    if route is None:
        raise exceptions.IdNotFoundError(
            models.Route, system_id=system_id, route_id=route_id
        )

    response = []
    trips = tripdam.list_all_in_route_by_pk(route.pk)
    trip_pk_to_last_stop = tripdam.get_trip_pk_to_last_stop_map(
        trip.pk for trip in trips
    )
    for trip in trips:
        trip_response = views.Trip.from_model(trip)
        last_stop = trip_pk_to_last_stop.get(trip.pk)
        if last_stop is not None:
            trip_response.last_stop = views.Stop.from_model(last_stop)
        response.append(trip_response)
    return response


@dbconnection.unit_of_work
def get_in_route_by_id(system_id, route_id, trip_id):
    """
    Get a representation for a trip in a system
    """
    trip = tripdam.get_in_route_by_id(system_id, route_id, trip_id)
    if trip is None:
        raise exceptions.IdNotFoundError(
            models.Trip, system_id=system_id, route_id=route_id, trip_id=trip_id
        )
    trip_response = views.Trip.from_model(trip)
    trip_response.route = views.Route.from_model(trip.route)
    trip_response.stop_times = []
    for stop_time in trip.stop_times:
        stop_time_response = views.TripStopTime.from_model(stop_time)
        stop_time_response.stop = views.Stop.from_model(stop_time.stop)
        trip_response.stop_times.append(stop_time_response)
    return trip_response
