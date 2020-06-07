import flask

from transiter.http.httpmanager import (
    http_endpoint,
    link_target,
    get_url_parameters,
    get_enum_url_parameter,
    HttpMethod,
    get_float_url_parameter,
)
from transiter.services import stopservice, views

stop_endpoints = flask.Blueprint(__name__, __name__)


@http_endpoint(stop_endpoints, "/systems/<system_id>/stops")
@link_target(views.StopsInSystem, ["_system_id"])
def list_all_in_system(system_id):
    return stopservice.list_all_in_system(
        system_id,
        alerts_detail=get_enum_url_parameter("alerts_detail", views.AlertsDetail),
    )


@http_endpoint(
    stop_endpoints, "/stops", method=HttpMethod.POST, returns_json_response=False
)
@http_endpoint(stop_endpoints, "/systems/<system_id>/stops", method=HttpMethod.POST)
def geographical_search(system_id=None):
    return stopservice.geographical_search(
        system_id=system_id,
        latitude=get_float_url_parameter("latitude", required=True),
        longitude=get_float_url_parameter("longitude", required=True),
        distance=get_float_url_parameter("distance", default=1000),
        return_service_maps=True,
    )


@http_endpoint(stop_endpoints, "/systems/<system_id>/stops/<stop_id>")
@link_target(views.Stop, ["_system_id", "id"])
def get_in_system_by_id(system_id, stop_id):
    """Retrieve a specific stop in a specific system."""
    request_args = get_url_parameters(
        ["minimum_number_of_trips", "include_all_trips_within", "exclude_trips_before"],
        error_if_extra_keys=False,
    )
    return stopservice.get_in_system_by_id(
        system_id,
        stop_id,
        alerts_detail=get_enum_url_parameter("alerts_detail", views.AlertsDetail),
        **request_args
    )
