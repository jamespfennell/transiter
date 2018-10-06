from ..database import accessobjects

stop_dao = accessobjects.StopDao()
stop_event_dao = accessobjects.StopEventDao()

def list_all_in_system(system_id):

    response = []

    for stop in stop_dao.list_all_in_system(system_id):
        response.append(stop.repr_for_list())
    return response

def google_maps_url(location):

    return 'https://www.google.com/maps/search/?api=1&query={}+Station+near+{},{}'.format(
        str.replace(location.name, ' ', '+'), location.lattitude, location.longitude)


class DirectionNamesMatcher:
    def __init__(self):
        self._directory = {None: {}}

    def match_stop_event(self, stop_event):
        track = stop_event.scheduled_track
        direction = stop_event.direction
        #print(self._directory)
        #print(direction)
        if track in self._directory and direction in self._directory[track]:
            return self._directory[track][direction]
        return self._directory[None][direction]


    def add_direction_name(self, direction_name):
        track = direction_name.track
        direction = direction_name.direction
        self._directory.setdefault(track, {})
        self._directory[track][direction] = direction_name.name

import time
def get_in_system_by_id(system_id, stop_id):

    stop = stop_dao.get_in_system_by_id(system_id, stop_id)
    response = stop.repr_for_list()

    direction_names_matcher = DirectionNamesMatcher()
    count = {}
    route_ids_so_far = {}
    direction_names_response = []
    for direction_name in stop.direction_names:
        direction_names_matcher.add_direction_name(direction_name)
        direction_names_response.append(direction_name.name)
        count[direction_name.name] = 0
        route_ids_so_far[direction_name.name] = set()
    response['direction_names'] = direction_names_response

    # TODO(use relationship instead and join)
    stop_events = stop_event_dao.get_by_stop_pri_key(stop.id)
    stop_event_responses = []
    for stop_event in stop_events:

        direction_name = direction_names_matcher.match_stop_event(stop_event)
        print(direction_name)
        if stop_event.departure_time is None:
            this_time = stop_event.arrival_time.timestamp()
        else:
            this_time = stop_event.departure_time.timestamp()

        count[direction_name] += 1
        # If this prediction should already have passed
        # TODO rethink this
        if this_time < time.time():
            continue

        # Rules for whether to append or not go here
        # If any of these condition are met the stop event will be appended
        # If there are less that 4 trip in this direction so far
        condition1 = (count[direction_name] <= 4)
        # If this trip is coming within 5 minutes
        condition2 = (this_time - time.time() <= 600)
        # If not trips of this route have been added so far
        condition3 = (stop_event.trip.route.route_id not in route_ids_so_far[direction_name])
        print(count)
        print('Considering {}'.format(stop_event.trip.trip_id))
        print([condition1, condition2, condition3])
        if not (condition1 or condition2 or condition3):
            print('Skipping {}'.format(stop_event.trip.trip_id))
            continue




        route_ids_so_far[direction_name]\
            .add(stop_event.trip.route.route_id)





        stop_event_response = {
            'direction_name': direction_name
        }
        stop_event_response.update(stop_event.repr_for_list())
        trip_response = stop_event.trip.repr_for_get()
        trip_response['route'] = stop_event.trip.route.repr_for_list()
        stop_event_response['trip'] = trip_response
        stop_event_responses.append(stop_event_response)
    response['stop_events'] = stop_event_responses
    station_response = stop.station.repr_for_list()
    station_response['system'] = 'NI'
    station_response['sibling_stops'] = []
    for sibling_stop in stop.station.stops:
        if sibling_stop.stop_id == stop_id:
            continue
        station_response['sibling_stops'].append(
            sibling_stop.repr_for_list()
        )
    # TODO use a Get parameter to specify a depth
    station_response['child_stations'] = []
    station_response['parent_station'] = None
    response['parent_station'] = station_response

    return response
