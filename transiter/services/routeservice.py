from ..data.dbaccessobjects import RouteDao

route_dao = RouteDao()


def list(system_id):

    response = []
    route_dao.system_id = system_id
    for route in route_dao.list():
        route_response = {
            'route_id': route.route_id,
            'service_status': 'not implemented',
            'href': 'not implemented'
            }
        response.append(route_response)
    return response


def get_by_id(system_id, route_id):
    # TODO: have verbose option

    route = route_dao.get_by_id(route_id, system_id)
    response = {
        'route_id': route.route_id,
        'frequency': 'not implemented',
        'color': route.color,
        'service_status': 'not implemented',
        'service_status_messages': 'not implemented',
        #'long_name': route.long_name,
        #'description': route.description,
        #'timetable_url': route.timetable_url,
        'stops': 'not implemented',
        'list_entries': []
        }
    """
    messages = route.status_messages
    for message in messages:
        message_response = {
            'type': message.message_type,
            'content': message.message
        }
        response['messages'].append(message_response)
    """
    for list_entry in route.list_entries:
        stop = list_entry.stop
        stop_response = {
            'stop_id': stop.stop_id,
            'name': stop.name
        }
        response['list_entries'].append(stop_response)

    return response
