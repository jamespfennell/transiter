"""
Realtime trips

Endpoints for getting data on realtime trips in a route.
"""

import flask

from transiter.http.httpmanager import (
    link_target,
    http_endpoint,
    get_enum_url_parameter,
)
from transiter.services import tripservice, views

trip_endpoints = flask.Blueprint(__name__, __name__)


@http_endpoint(trip_endpoints, "")
def list_all_in_route(system_id, route_id):
    """
    List trips in a route

    List all the realtime trips in a particular route.

    Return code     | Description
    ----------------|-------------
    `200 OK`        | Returned if the system and route exist.
    `404 NOT FOUND` | Returned if either the system or the route does not exist.
    """
    return tripservice.list_all_in_route(
        system_id,
        route_id,
        alerts_detail=get_enum_url_parameter("alerts_detail", views.AlertsDetail),
    )


@http_endpoint(trip_endpoints, "/<trip_id>")
@link_target(views.Trip, ["_system_id", "_route_id", "id"])
def get_in_route_by_id(system_id, route_id, trip_id):
    """
    Get a trip in a route

    Describe a trip in a route in a transit system.

    Return code         | Description
    --------------------|-------------
    `200 OK`            | Returned if the system, route and trip exist.
    `404 NOT FOUND`     | Returned if the system, route or trip do not exist.
    """
    return tripservice.get_in_route_by_id(
        system_id,
        route_id,
        trip_id,
        alerts_detail=get_enum_url_parameter("alerts_detail", views.AlertsDetail),
    )
