from transiter.database.daos import route_dao
from transiter.utils import linksutil

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
        route_response = route.short_repr()
        route_response.update({
            'service_status': _construct_status(route),
            'href': linksutil.RouteEntityLink(route)
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
    response = route.long_repr()
    response.update({
        'frequency': _construct_frequency(route),
        'service_status': _construct_status(route),
        'service_status_messages':
            [message.short_repr() for message in route.route_statuses],
        'stops': []
        })
    current_stop_ids = list(route_dao.get_active_stop_ids(route.id))

    default_service_pattern = route.default_service_pattern

    for entry in default_service_pattern.vertices:
        stop_response = entry.stop.short_repr()
        stop_response.update({
            'current_service': stop_response['stop_id'] in current_stop_ids,
            'position': entry.position,
            'href': linksutil.StopEntityLink(entry.stop)
        })
        response['stops'].append(stop_response)
    return response


def _construct_frequency(route):
    terminus_data = route_dao.get_terminus_data(route.id)
    total_count = 0
    total_seconds = 0
    for (earliest_time, latest_time, count, __) in terminus_data:
        if count <= 2:
            continue
        total_count += count
        total_seconds += (latest_time.timestamp()-earliest_time.timestamp())*count/(count-1)
        #print(total_count, total_seconds)
    if total_count == 0:
        return None
    else:
        return (total_seconds/total_count)/60



def _construct_status(route):
    """
    Constructs the status for a route. This is defined as the message type of
    the highest priority message.
    :param route: a model.Route object
    :return: a string
    """
    status = None
    priority = -100000
    for message in route.route_statuses:
        if message.status_priority > priority:
            status = message.status_type
            priority = message.status_priority
    if status is None:
        status = 'Good Service'
    return status
