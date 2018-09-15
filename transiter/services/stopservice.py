from ..data import stopdam


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

def get(stop_id):

    stop = stopdam.get(stop_id)
    response = {
        'stop_id': stop.stop_id,
        'name': stop.name,
        'longitude': str(stop.longitude),
        'lattitude': str(stop.lattitude),
        'google_maps_url': google_maps_url(stop)
        }

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
