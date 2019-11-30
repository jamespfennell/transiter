import flask

from transiter.http.httpmanager import link_target, http_endpoint
from transiter.services import tripservice, links

trip_endpoints = flask.Blueprint(__name__, __name__)


@http_endpoint(trip_endpoints, "")
def list_all_in_route(system_id, route_id):
    """List all trips for a specific system"""
    return tripservice.list_all_in_route(system_id, route_id)


@http_endpoint(trip_endpoints, "/<trip_id>")
@link_target(links.TripEntityLink)
def get_in_route_by_id(system_id, route_id, trip_id):
    """Retrieve a specific trip in a specific system."""
    return tripservice.get_in_route_by_id(system_id, route_id, trip_id)
