
from ..database.accessobjects import TripDao
trip_dao = TripDao()


def list_all_in_route(system_id, route_id):
    return [trip.repr_for_list() for trip in trip_dao.list_all_in_route(system_id, route_id)]



def get_in_route_by_id(system_id, route_id, trip_id):
    trip = trip_dao.get_in_route_by_id(system_id, route_id, trip_id)
    trip_response = trip.repr_for_get()
    trip_response['stop_events'] = []
    for stop_event in trip.stop_events:
        stop_event_response = stop_event.repr_for_list()
        stop_event_response['stop'] = stop_event.stop.repr_for_list()
        trip_response['stop_events'].append(stop_event_response)
    return trip_response
