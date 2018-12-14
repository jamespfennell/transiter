from transiter.data import database
from transiter.data.dams import stopdam, servicepatterndam
from transiter.utils import linksutil


@database.unit_of_work
def list_all_in_system(system_id):

    response = []

    for stop in stopdam.list_all_in_system(system_id):
        stop_response = stop.short_repr()
        stop_response.update({
            'href': linksutil.StopEntityLink(stop)
        })
        response.append(stop_response)
    return response


class _DirectionNameMatcher:
    def __init__(self, rules):
        self._rules = rules
        self._cache = {}
        for rule in self._rules:
            print((rule.stop_pk, rule.direction_id, rule.track, rule.name))

    def all_names(self):
        return {rule.name for rule in self._rules}

    def match(self, stop_event):
        #print(self._rules)
        #print(self._cache)
        stop = stop_event.stop
        #print(stop.pk)
        cache_key = (
            stop.pk,
            stop_event.trip.direction_id,
            stop_event.track)
        if cache_key not in self._cache:
            for rule in self._rules:
                #print((rule.stop_pk, rule.direction_id, rule.track, rule.name))
                if rule.stop_pk != cache_key[0]:
                    continue
                if rule.direction_id is not None and rule.direction_id != cache_key[1]:
                    continue
                if rule.track is not None and rule.track != cache_key[2]:
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
        #if this_time < time.time():
        #    return True

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


def _get_stop_descendants(stop):
    descendants = [child_stop for child_stop in stop.child_stops]
    for child_stop in stop.child_stops:
        descendants.extend(_get_stop_descendants(child_stop))
    return descendants


def _get_stop_ancestors(stop):
    if stop.parent_stop is None:
        return []
    ancestors = [stop.parent_stop]
    for child_stop in stop.parent_stop.child_stops:
        if stop.id == child_stop.id:
            continue
        ancestors.append(child_stop)
    ancestors.extend(_get_stop_ancestors(stop.parent_stop))
    return ancestors


@database.unit_of_work
def get_in_system_by_id(system_id, stop_id):

    # TODO: make the service pattern dao retrieve by pk
    # TODO: make a default_trip_at_stop function????
    # TODO make this more robust for stops without direction names
    stop = stopdam.get_in_system_by_id(system_id, stop_id)

    descendants = _get_stop_descendants(stop)
    direction_name_rules = []
    direction_name_rules.extend(stop.direction_name_rules)
    for descendant in descendants:
        direction_name_rules.extend(descendant.direction_name_rules)
    all_stop_pks = {stop.pk}
    all_stop_pks.update(stop.pk for stop in descendants)

    total_stop_pks = [stop_pk for stop_pk in all_stop_pks]
    total_stop_pks.extend([s.pk for s in _get_stop_ancestors(stop)])
    default_routes_map = servicepatterndam.get_default_routes_at_stops_map(total_stop_pks)
    #default_routes = service_pattern_dao.get_default_trips_at_stops(total_stop_pks)
    default_routes = {}
    for stop_pk in total_stop_pks:
        default_routes[stop_pk] = [route.id for route in default_routes_map[stop_pk]]
    #default_routes = {stop_pk: default_routes_map[stop_pk].id for stop_pk in total_stop_pks}

    stop_event_filter = _StopEventFilter()
    direction_name_matcher = _DirectionNameMatcher(direction_name_rules)
    response = {
        **stop.short_repr(),
        'usual_routes': default_routes[stop.pk],
        'direction_names': list(direction_name_matcher.all_names()),
        'stop_events': []
    }

    stop_events = stopdam.list_stop_time_updates_at_stops(all_stop_pks)
    for stop_event in stop_events:
        direction_name = direction_name_matcher.match(stop_event)
        if stop_event_filter.exclude(stop_event, direction_name):
            continue
        stop_event_response = {
            'stop_id': stop_event.stop.id,
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

    response['child_stops'] = _child_stops_repr(stop, default_routes)
    response['parent_stop'] = _parent_stop_repr(stop, default_routes)

    return response


def _child_stops_repr(stop, default_routes):
    repr = []
    for child_stop in stop.child_stops:
        repr.append({
            **child_stop.short_repr(),
            'usual_routes': default_routes[child_stop.pk],
            'href': linksutil.StopEntityLink(child_stop),
            'child_stops': _child_stops_repr(child_stop, default_routes)
        })
    return repr


def _parent_stop_repr(stop, default_routes):
    if stop.parent_stop is None:
        return None
    repr = {
        **stop.parent_stop.short_repr(),
        'usual_routes': default_routes[stop.parent_stop.pk],
        'href': linksutil.StopEntityLink(stop.parent_stop),
        'child_stops': [],
        'parent_stop': _parent_stop_repr(stop.parent_stop, default_routes)
    }
    for child_stop in stop.parent_stop.child_stops:
        if stop.id == child_stop.id:
            continue
        repr['child_stops'].append({
            **child_stop.short_repr(),
            'usual_routes': default_routes[child_stop.pk],
            'href': linksutil.StopEntityLink(child_stop)
        })
    return repr

