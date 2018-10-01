from ..data import dbaccessobjects

stop_dao = dbaccessobjects.StopDao()
stop_event_dao = dbaccessobjects.StopEventDao()

def list_all_in_system(system_id):

    response = []

    for stop in stop_dao.list_all_in_system(system_id):
        stop_response = {
            'stop_id': stop.stop_id,
            'name': stop.name
            }
        response.append(stop_response)
    return response

def google_maps_url(location):

    return 'https://www.google.com/maps/search/?api=1&query={}+Station+near+{},{}'.format(
        str.replace(location.name, ' ', '+'), location.lattitude, location.longitude)

def get_in_system_by_id(system_id, stop_id):

    stop = stop_dao.get_in_system_by_id(system_id, stop_id)
    response = {
        'stop_id': stop.stop_id,
        'name': stop.name
        # If there is a verbose option...
        #'longitude': str(stop.longitude),
        #'lattitude': str(stop.lattitude),
        #'google_maps_url': google_maps_url(stop)
        }

    print('Here')
    stop_events = stop_event_dao.get_by_stop_pri_key(stop.id)
    stop_event_responses = []
    for stop_event in stop_events:
        stop_event_response = {
            'trip': {
                'route_id': stop_event.trip.route.route_id
            },
            'arrival_time': stop_event.arrival_time
        }
        stop_event_responses.append(stop_event_response)
        print(stop_event)
    response['stop_events'] = stop_event_responses
    return response
    station_response = {
        'station_id': stop.station.id,
        'other_stops': [],
        }
    for sibling_stop in stop.station.stops:
        if sibling_stop.stop_id == stop_id:
            continue
        station_response['other_stops'].append({
            'stop_id': sibling_stop.stop_id,
            'name': sibling_stop.name,
            'regular_service': 'XYZ'
        })
    response['station'] = station_response

    direction_names_response = []
    for direction_name in stop.direction_names:
        direction_names_response.append({
            'name': direction_name.name,
            'trips': []
        })
    response['directions'] = direction_names_response

    return response
