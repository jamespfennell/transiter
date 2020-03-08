import flask

from transiter.http.httpmanager import http_endpoint, link_target, get_url_parameters
from transiter.services import stopservice, links

stop_endpoints = flask.Blueprint(__name__, __name__)


@http_endpoint(stop_endpoints, "")
@link_target(links.StopsInSystemIndexLink)
def list_all_in_system(system_id):
    """List all stops for a specific system."""
    return stopservice.list_all_in_system(system_id)


@http_endpoint(stop_endpoints, "/<stop_id>")
@link_target(links.StopEntityLink)
def get_in_system_by_id(system_id, stop_id):
    """Retrieve a specific stop in a specific system."""
    request_args = get_url_parameters(
        ["minimum_number_of_trips", "include_all_trips_within", "exclude_trips_before"]
    )
    return stopservice.get_in_system_by_id(system_id, stop_id, **request_args)
