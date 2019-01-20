from transiter.data import database
from transiter.data.dams import tripdam
from transiter.general import linksutil, exceptions


@database.unit_of_work
def list_all_in_route(system_id, route_id):
    """
    Get representations for all trips in a system.
    :param system_id: the text id of the system
    :param route_id: the route id of the system
    :return: a list of short model.Trip representations.

    .. code-block:: json

        [
            {
                <fields in a short model.Trip representation>,
            },
            ...
        ]

    """
    response = []
    trips = list(tripdam.list_all_in_route(system_id, route_id))
    trip_pk_to_last_stop = tripdam.get_trip_pk_to_last_stop_map(
        trip.pk for trip in trips
    )
    for trip in trips:
        last_stop = trip_pk_to_last_stop.get(trip.pk)
        trip_response = {
            **trip.short_repr(),
            "last_stop": {
                **last_stop.short_repr(),
                'href': linksutil.StopEntityLink(last_stop)
            },
            'href': linksutil.TripEntityLink(trip),
        }
        response.append(trip_response)
    return response


@database.unit_of_work
def get_in_route_by_id(system_id, route_id, trip_id):
    """
    Get a representation for a trip in a system
    :param system_id: the text id of the system
    :param route_id: the text id of the route
    :param trip_id: the text id of the route
    :return: a long model.Trip representation with an additional field
    'stop_events' containing a list of short model.StopEvent representations.
    Each of the model.StopEvent representations contains an additional field
    'stop' containing a short representation of the associated model.Stop.
    {
        <fields in a long model.Trip representation>,
        'stop_events': [
            {
                <fields in a short model.StopEvent representation>
                'stop': {
                    <fields in a short model.Stop representation>
                }
            },
            ...
        ]
    """
    trip = tripdam.get_in_route_by_id(system_id, route_id, trip_id)
    if trip is None:
        raise exceptions.IdNotFoundError
    trip_response = {
        **trip.long_repr(),
        'route': {
            **trip.route.short_repr(),
            'href': linksutil.RouteEntityLink(trip.route)
        },
        'stop_events': [
            {
                **stu.short_repr(),
                'stop': {
                    **stu.stop.short_repr(),
                    'href': linksutil.StopEntityLink(stu.stop)
                }
            }
            for stu in trip.stop_events
        ],
    }
    return trip_response
