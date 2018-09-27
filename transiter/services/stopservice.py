from ..data import dbaccessobjects

stop_dao = dbaccessobjects.StopDao()
stop_event_dao = dbaccessobjects.StopEventDao()

def list():

    response = []

    for stop in stopdam.list():
        stop_response = {
            'stop_id': stop.stop_id,
            'name': stop.name
            }
        response.append(stop_response)
    return response

def google_maps_url(location):

    return 'https://www.google.com/maps/search/?api=1&query={}+Station+near+{},{}'.format(
        str.replace(location.name, ' ', '+'), location.lattitude, location.longitude)

def get_by_id(system_id, stop_id):

    stop = stop_dao.get_by_id(stop_id, system_id)
    response = {
        'stop_id': stop.stop_id,
        'name': stop.name,
        'longitude': str(stop.longitude),
        'lattitude': str(stop.lattitude),
        'google_maps_url': google_maps_url(stop)
        }

    print('Here')
    stop_events = stop_event_dao.get_by_stop_pri_key(stop.id)
    for stop_event in stop_events:
        print(stop_event)

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
