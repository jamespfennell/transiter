from transiter.data import database
from transiter.data.dams import routedam, systemdam
from transiter.general import linksutil, exceptions


@database.unit_of_work
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
    system = systemdam.get_by_id(system_id)
    if system is None:
        raise exceptions.IdNotFoundError
    response = []
    routes = list(routedam.list_all_in_system(system_id))
    route_statuses = routedam.list_route_statuses(route.pk for route in routes)
    for route in routes:
        route_response = route.short_repr()
        route_response.update({
            'service_status': route_statuses[route.pk],
            'href': linksutil.RouteEntityLink(route)
        })
        response.append(route_response)
    return response


@database.unit_of_work
def get_in_system_by_id(system_id, route_id):
    """
    Get a representation for a route in the system
    :param system_id: the system's text id
    :param route_id: the route's text id
    :return:
    """
    # TODO: have verbose option
    return_links = False

    route = routedam.get_in_system_by_id(system_id, route_id)
    if route is None:
        raise exceptions.IdNotFoundError
    response = route.long_repr()
    route_status = routedam.list_route_statuses([route.pk]).get(route.pk)

    frequency = routedam.calculate_frequency(route.pk)
    if frequency is not None:
        frequency = int(frequency/6)/10
    response.update({
        'frequency': frequency,
        'service_status': route_status,
        'service_status_messages':
            [message.short_repr() for message in route.route_statuses],
        'service_maps': []
        })

    # TODO: also return empty service maps? Or should this be in the db?
    for service_map in route.service_patterns:
        if not service_map.group.use_for_stops_in_route:
            continue
        service_map_response = {
            'group_id': service_map.group.id,
            'stops': []
        }
        for entry in service_map.vertices:
            stop_response = entry.stop.short_repr()
            if return_links:
                stop_response.update({
                    'href': linksutil.StopEntityLink(entry.stop)
                })
            service_map_response['stops'].append(stop_response)
        response['service_maps'].append(service_map_response)

    return response


def _construct_frequency(route):
    terminus_data = routedam.calculate_frequency(route.pk)
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
        return int((total_seconds/total_count)/6)/10

