from ..database.accessobjects import RouteDao

route_dao = RouteDao()

def _construct_status(route):
    status = None
    priority = -100000
    for message in route.status_messages:
        if message.priority > priority:
            status = message.message_type
            priority = message.priority
    if status is None:
        status = 'Good Service'
    return status


def list_all_in_system(system_id):

    response = []
    for route in route_dao.list_all_in_system(system_id):
        route_response = route.repr_for_list()
        route_response.update({
            'service_status': _construct_status(route)
        })
        response.append(route_response)
    return response


def get_in_system_by_id(system_id, route_id):
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
