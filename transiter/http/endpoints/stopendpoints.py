"""
Stations and stops

Endpoints for getting data on stations and stops.
"""


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
    """
    List stops in a system

    List all the stops in a transit system.

    Return code     | Description
    ----------------|-------------
    `200 OK`        | Returned if the system with this ID exists.
    `404 NOT FOUND` | Returned if no system with the provided ID is installed.
    """
    return stopservice.list_all_in_system(
        system_id,
        alerts_detail=get_enum_url_parameter("alerts_detail", views.AlertsDetail),
    )


@http_endpoint(stop_endpoints, "/stops", method=HttpMethod.POST)
def geographical_search():
    """
    Search for stops

    Search for stops in all systems based on their proximity to a geographic root location.
    This endpoint can be used, for example, to list stops near a user given the user's location.

    It takes three URL parameters:

    - `latitude` - the latitude of the root location (required).
    - `longitude` - the longitude of the root location (required).
    - `distance` - the maximum distance, in meters, away from the root location that stops can be.
                This is optional and defaults to 1000 meters (i.e., 1 kilometer). 1 mile is about 1609 meters.

    The result of this endpoint is a list of stops ordered by distance, starting with the stop
    closest to the root location.
    """
    return _geographical_search_helper(None)


@http_endpoint(stop_endpoints, "/systems/<system_id>/stops", method=HttpMethod.POST)
def geographical_search_in_system(system_id):
    """
    Search for stops in a system

    Search for stops in a system based on their proximity to a geographic root location.
    This endpoint can be used, for example, to list stops near a user given the user's location.

    It takes three URL parameters:

    - `latitude` - the latitude of the root location (required).
    - `longitude` - the longitude of the root location (required).
    - `distance` - the maximum distance, in meters, away from the root location that stops can be.
                This is optional and defaults to 1000 meters (i.e., 1 kilometer). 1 mile is about 1609 meters.

    The result of this endpoint is a list of stops ordered by distance, starting with the stop
    closest to the root location.
    """
    return _geographical_search_helper(system_id)


def _geographical_search_helper(system_id):
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
    """
    Get a stop in a system

    Describe a stop in a transit system.

    Return code         | Description
    --------------------|-------------
    `200 OK`            | Returned if the system and stop exist.
    `404 NOT FOUND`     | Returned if either the system or the stop does not exist.
    """
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
