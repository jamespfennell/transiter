from ..data import routedata


def list():

    response = []

    for route in routedata.list():
        route_response = {
            'route_id': route.route_id
            }
        response.append(route_response)
    return response


def get(route_id):

    route = routedata.get(route_id)
    response = {
        'route_id': route.route_id,
        'short_name': route.short_name,
        'long_name': route.long_name,
        'description': route.description,
        'timetable_url': route.timetable_url,
        'color': route.color
        }
    return response

