from ..database.accessobjects import RouteDao

route_dao = RouteDao()


def list_all_in_system(system_id):
    """
    Get representations for all routes in a system.
    :param system_id: the text id of the system
    :return: a list of short model.Route representations with an additional
    'service_status' entry describing the current status.

    .. code-block:: json

        [
            {
                <fields in a short model.Route representation>,
                'service_status': <service status>
            },
            ...
        ]

    """
    response = []
    for route in route_dao.list_all_in_system(system_id):
        route_response = route.repr_for_list()
        route_response.update({
            'service_status': _construct_status(route)
        })
        response.append(route_response)
    return response


def get_in_system_by_id(system_id, route_id):
    """
    Get a representation for a route in the system
    :param system_id: the system's text id
    :param route_id: the route's text id
    :return:
    """
    # TODO: have verbose option

    route = route_dao.get_in_system_by_id(system_id, route_id)
    response = route.repr_for_get()
    response.update({
        'service_status': _construct_status(route),
        'service_status_messages':
            [message.repr_for_list() for message in route.status_messages],
        'stops': []
        })
    current_stop_ids = list(route_dao.get_active_stop_ids(route.id))
    for index, entry in enumerate(route.list_entries):
        stop_response = entry.stop.repr_for_list()
        stop_response.update({
            'current_service': stop_response['stop_id'] in current_stop_ids,
            'index': index
        })
        response['stops'].append(stop_response)
    return response


def _construct_status(route):
    """
    Constructs the status for a route. This is defined as the message type of
    the highest priority message.
    :param route: a model.Route object
    :return: a string
    """
    status = None
    priority = -100000
    for message in route.status_messages:
        if message.priority > priority:
            status = message.message_type
            priority = message.priority
    if status is None:
        status = 'Good Service'
    return status
