from transiter import exceptions
from transiter.data import dbconnection
from transiter.data.dams import tripdam, routedam
from transiter.services import links


@dbconnection.unit_of_work
def list_all_in_route(system_id, route_id, return_links=False):
    """
    Get representations for all trips in a system.

    :param system_id: the text id of the system
    :param route_id: the route id of the system
    :param return_links: whether to return links
    :return: a list of short model.Trip representations.
    """
    route = routedam.get_in_system_by_id(system_id, route_id)
    if route is None:
        raise exceptions.IdNotFoundError

    response = []
    trips = tripdam.list_all_in_route_by_pk(route.pk)
    trip_pk_to_last_stop = tripdam.get_trip_pk_to_last_stop_map(
        trip.pk for trip in trips
    )
    for trip in trips:
        last_stop = trip_pk_to_last_stop.get(trip.pk)
        trip_response = {**trip.short_repr(), "last_stop": last_stop.short_repr()}
        if return_links:
            trip_response["href"] = links.TripEntityLink(trip)
            trip_response["last_stop"]["href"] = links.StopEntityLink(last_stop)
        response.append(trip_response)
    return response


@dbconnection.unit_of_work
def get_in_route_by_id(system_id, route_id, trip_id, return_links=False):
    """
    Get a representation for a trip in a system

    :param system_id: the text id of the system
    :param route_id: the text id of the route
    :param trip_id: the text id of the route
    :param return_links: whether to return links
    """
    trip = tripdam.get_in_route_by_id(system_id, route_id, trip_id)
    if trip is None:
        raise exceptions.IdNotFoundError
    trip_response = {
        **trip.long_repr(),
        "route": trip.route.short_repr(),
        "stop_time_updates": [],
    }
    if return_links:
        trip_response["route"]["href"] = links.RouteEntityLink(trip.route)
    for stop_time in trip.stop_times:
        stop_time_response = {
            **stop_time.short_repr(),
            "stop": stop_time.stop.short_repr(),
        }
        if return_links:
            stop_time_response["stop"]["href"] = links.StopEntityLink(stop_time.stop)
        trip_response["stop_time_updates"].append(stop_time_response)
    return trip_response
