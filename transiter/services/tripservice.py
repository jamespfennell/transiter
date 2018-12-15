from transiter.data.dams import tripdam
from transiter.general import linksutil

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
    for trip in tripdam.list_all_in_route(system_id, route_id):
        trip_response = trip.short_repr()
        trip_response.update({
            "origin": {
                "stop_id": "NI",
                "name": "NI",
                'location': 'NI',
                "usual_service": "NI",
                "href": "NI"
            },
            "terminus": {
                "stop_id": "NI",
                "name": "NI",
                'location': 'NI',
                "usual_service": "NI",
                "href": "NI"
            },
            'href': linksutil.TripEntityLink(trip),
        })
        response.append(trip_response)
    return response


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
    trip_response = trip.long_repr()
    trip_response['stop_events'] = []
    for stop_event in trip.stop_events:
        stop_event_response = stop_event.short_repr()
        stop_event_response['future'] = stop_event.future
        stop_event_response['stop'] = stop_event.stop.short_repr()
        stop_event_response['stop']['href'] = linksutil.StopEntityLink(stop_event.stop)
        trip_response['stop_events'].append(stop_event_response)
    return trip_response
