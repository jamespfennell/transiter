from transiter.database.daos import stop_dao, stop_event_dao, service_pattern_dao
from transiter.utils import linksutil

def list_all_in_system(system_id):

    response = []

    for stop in stop_dao.list_all_in_system(system_id):
        stop_response = stop.short_repr()
        stop_response.update({
            'href': linksutil.StopEntityLink(stop)
        })
        response.append(stop_response)
    return response

"""
def google_maps_url(location):

    return 'https://www.google.com/maps/search/?api=1&query={}+Station+near+{},{}'.format(
        str.replace(location.name, ' ', '+'), location.lattitude, location.longitude)
"""



class DirectionNameMatcher:
    def __init__(self, rules):
        self._rules = rules
        self._cache = {}

    def all_names(self):
        return {rule.name for rule in self._rules}

    def match(self, stop, stop_event):
        cache_key = (
            stop.id,
            stop_event.trip.direction_id,
            stop_event.track,
            stop_event.stop_id_alias)
        print(cache_key)
        if cache_key not in self._cache:
            for rule in self._rules:
                print(rule.stop_pk, rule.direction_id, rule.track, rule.stop_id_alias)
                if rule.stop_pk != cache_key[0]:
                    continue
                if rule.direction_id is not None and rule.direction_id != cache_key[1]:
                    continue
                if rule.track is not None and rule.track != cache_key[2]:
                    continue
                if rule.stop_id_alias is not None and rule.stop_id_alias != cache_key[3]:
                    continue
                self._cache[cache_key] = rule.name
                break

        if cache_key not in self._cache:
            self._cache[cache_key] = 'CNM!'

        return self._cache[cache_key]


import time
def get_in_system_by_id(system_id, stop_id):

    # TODO make this more robust for stops without direction names
    stop = stop_dao.get_in_system_by_id(system_id, stop_id)
    response = stop.short_repr()
    response.update({
        'usual_routes': service_pattern_dao.get_default_trips_at_stops(
            [stop_id])[stop_id]
    })
    direction_name_rules = stop.direction_name_rules
    direction_name_matcher = DirectionNameMatcher(direction_name_rules)
    count = {None: 0}
    route_ids_so_far = {None: set()}
    direction_names_response = []
    for direction_name in direction_name_matcher.all_names():
        direction_names_response.append(direction_name)
        count[direction_name] = 0
        route_ids_so_far[direction_name] = set()
    response['direction_names'] = direction_names_response

    # TODO(use relationship instead and join)
    stop_events = stop_event_dao.get_by_stop_pri_key(stop.id)
    #print(len(list(stop_events)))
    stop_event_responses = []
    for stop_event in stop_events:

        direction_name = direction_name_matcher.match(stop, stop_event)
        #print(direction_name)
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
        #print(count)
        #print('Considering {}'.format(stop_event.trip.trip_id))
        #print([condition1, condition2, condition3])
        if not (condition1 or condition2 or condition3):
            #print('Skipping {}'.format(stop_event.trip.trip_id))
            continue




        route_ids_so_far[direction_name]\
            .add(stop_event.trip.route.route_id)





        stop_event_response = {
            'direction_name': direction_name
        }
        stop_event_response.update(stop_event.short_repr())
        trip_response = stop_event.trip.long_repr()
        trip_response['route'] = stop_event.trip.route.short_repr()
        trip_response['route']['href'] = linksutil.RouteEntityLink(stop_event.trip.route)
        trip_response['origin'] = 'NI'
        trip_response['terminus'] = 'NI'
        trip_response['href'] = linksutil.TripEntityLink(stop_event.trip)
        stop_event_response['trip'] = trip_response
        stop_event_responses.append(stop_event_response)
    response['stop_events'] = stop_event_responses
    station_response = stop.station.short_repr()
    station_response['system'] = 'NI'
    station_response['href'] = 'NI'
    station_response['child_stops'] = []
    for sibling_stop in stop.station.stops:
        if sibling_stop.stop_id == stop_id:
            continue
        child_response = sibling_stop.short_repr()
        child_response.update({
            'usual_routes': service_pattern_dao.get_default_trips_at_stops(
                [sibling_stop.stop_id])[sibling_stop.stop_id]
        })
        station_response['child_stops'].append(
            child_response
        )
    # TODO use a Get parameter to specify a depth
    station_response['child_stations'] = []
    station_response['parent_station'] = None
    response['parent_station'] = station_response

    return response
