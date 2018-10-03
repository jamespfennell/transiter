
from ..database.accessobjects import TripDao

trip_dao = TripDao()


def list_all_in_route(system_id, route_id):
    return [trip.repr_for_list() for trip in trip_dao.list_all_in_route(system_id, route_id)]



def get_in_route_by_id(system_id, route_id, trip_id):
    trip = trip_dao.get_in_route_by_id(system_id, route_id, trip_id)
    return trip.repr_for_get()