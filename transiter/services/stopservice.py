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


class _DirectionNameMatcher:
    def __init__(self, rules):
        self._rules = rules
        self._cache = {}

    def all_names(self):
        return {rule.name for rule in self._rules}

    def match(self, stop, stop_event):
        cache_key = (
            stop.pk,
            stop_event.trip.direction_id,
            stop_event.track,
            stop_event.stop_id_alias)
        if cache_key not in self._cache:
            for rule in self._rules:
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
            self._cache[cache_key] = None

        return self._cache[cache_key]


import time


class _StopEventFilter:

    def __init__(self):
        self._count = {}
        self._route_ids_so_far = {}
        pass

    def _add_direction_name(self, direction_name):
        if direction_name in self._count:
            return
        self._count[direction_name] = 0
        self._route_ids_so_far[direction_name] = set()

    def exclude(self, stop_event, direction_name):
        self._add_direction_name(direction_name)

        if stop_event.departure_time is None:
            this_time = stop_event.arrival_time.timestamp()
        else:
            this_time = stop_event.departure_time.timestamp()

        self._count[direction_name] += 1
        # If this prediction should already have passed
        # TODO rethink this
        if this_time < time.time():
            return True

        # Rules for whether to append or not go here
        # If any of these condition are met the stop event will be appended
        # If there are less that 4 trip in this direction so far
        condition1 = (self._count[direction_name] <= 4)
        # If this trip is coming within 5 minutes
        condition2 = (this_time - time.time() <= 600)
        # If not trips of this route have been added so far
        condition3 = (stop_event.trip.route.id not in self._route_ids_so_far[direction_name])

        self._route_ids_so_far[direction_name] \
            .add(stop_event.trip.route.id)
        return (not (condition1 or condition2 or condition3))


def get_in_system_by_id(system_id, stop_id):

    # TODO: make the service pattern dao retrieve by pk
    # TODO: make a default_trip_at_stop function
    # TODO make this more robust for stops without direction names
    stop = stop_dao.get_in_system_by_id(system_id, stop_id)
    stop_event_filter = _StopEventFilter()
    direction_name_matcher = _DirectionNameMatcher(stop.direction_name_rules)
    response = {
        **stop.short_repr(),
        'usual_routes': service_pattern_dao.get_default_trips_at_stops(
            [stop_id])[stop_id],
        'direction_names': list(direction_name_matcher.all_names()),
        'stop_events': []
    }

    stop_events = stop_event_dao.get_by_stop_pri_key(stop.pk)
    for stop_event in stop_events:
        direction_name = direction_name_matcher.match(stop, stop_event)
        if stop_event_filter.exclude(stop_event, direction_name):
            continue
        stop_event_response = {
            'direction_name': direction_name,
            **(stop_event.short_repr()),
            'trip': {
                **(stop_event.trip.long_repr()),
                'route': {
                    **(stop_event.trip.route.short_repr()),
                    'href': linksutil.RouteEntityLink(stop_event.trip.route),
                },
                'href': linksutil.TripEntityLink(stop_event.trip),
            }
        }
        response['stop_events'].append(stop_event_response)

    return response


"""
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
# TODO enable parent station
#response['parent_station'] = station_response
"""

