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
    return tripservice.list_all_in_route(
        system_id,
        route_id,
        alerts_detail=get_enum_url_parameter("alerts_detail", views.AlertsDetail),
    )


@http_endpoint(trip_endpoints, "/<trip_id>")
@link_target(views.Trip, ["_system_id", "_route_id", "id"])
def get_in_route_by_id(system_id, route_id, trip_id):
    return tripservice.get_in_route_by_id(
        system_id,
        route_id,
        trip_id,
        alerts_detail=get_enum_url_parameter("alerts_detail", views.AlertsDetail),
    )
