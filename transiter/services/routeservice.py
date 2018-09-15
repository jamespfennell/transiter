from ..data import routedam


def list():

    response = []

    for route in routedam.list():
        route_response = {
            'route_id': route.route_id
            }
        response.append(route_response)
    return response


def get(route_id):

    route = routedam.get(route_id)
    response = {
        'route_id': route.route_id,
        'short_name': route.short_name,
        'long_name': route.long_name,
        'description': route.description,
        'timetable_url': route.timetable_url,
        'color': route.color,
        'messages': []
        }
    messages = route.status_messages
    for message in messages:
        message_response = {
            'type': message.message_type,
            'content': message.message
        }
        response['messages'].append(message_response)

    return response
