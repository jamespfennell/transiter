from transiter.database.accessobjects import TripDao

trip_dao = TripDao()


def list_all_in_route(system_id, route_id):
    """
    Get representations for all trips in a system.
    :param system_id: the text id of the system
    :param route_id: the route id of the system
    :return: a list of short model.Trip representations.
    [
        {
            <fields in a long model.Trip representation>,
        },
        ...
    ]
    """
    return [trip.repr_for_list()
            for trip
            in trip_dao.list_all_in_route(system_id, route_id)]


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
    trip = trip_dao.get_in_route_by_id(system_id, route_id, trip_id)
    trip_response = trip.repr_for_get()
    trip_response['stop_events'] = []
    for stop_event in trip.stop_events:
        stop_event_response = stop_event.repr_for_list()
        stop_event_response['stop'] = stop_event.stop.repr_for_list()
        trip_response['stop_events'].append(stop_event_response)
    return trip_response
