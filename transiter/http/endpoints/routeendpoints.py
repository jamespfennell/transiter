"""
Routes

Endpoints for getting data on transit system routes.
"""
import flask

from transiter.http.httpmanager import (
    http_endpoint,
    link_target,
    get_enum_url_parameter,
)
from transiter.services import routeservice, views

route_endpoints = flask.Blueprint(__name__, __name__)


@http_endpoint(route_endpoints, "")
@link_target(views.RoutesInSystem, ["_system_id"])
def list_all_in_system(system_id):
    """
    List routes in a system

    List all the routes in a transit system.

    Return code     | Description
    ----------------|-------------
    `200 OK`        | Returned if the system with this ID exists.
    `404 NOT FOUND` | Returned if no system with the provided ID is installed.
    """
    return routeservice.list_all_in_system(
        system_id,
        alerts_detail=get_enum_url_parameter("alerts_detail", views.AlertsDetail),
    )


@http_endpoint(route_endpoints, "/<route_id>")
@link_target(views.Route, ["_system_id", "id"])
def get_in_system_by_id(system_id, route_id):
    """
    Get a route in a system

    Describe a route in a transit system.

    Return code         | Description
    --------------------|-------------
    `200 OK`            | Returned if the system and route exist.
    `404 NOT FOUND`     | Returned if either the system or the route does not exist.
    """
    return routeservice.get_in_system_by_id(
        system_id,
        route_id,
        alerts_detail=get_enum_url_parameter("alerts_detail", views.AlertsDetail),
    )
