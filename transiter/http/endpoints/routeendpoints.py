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
    return routeservice.list_all_in_system(
        system_id,
        alerts_detail=get_enum_url_parameter("alerts_detail", views.AlertsDetail),
    )


@http_endpoint(route_endpoints, "/<route_id>")
@link_target(views.Route, ["_system_id", "id"])
def get_in_system_by_id(system_id, route_id):
    return routeservice.get_in_system_by_id(
        system_id,
        route_id,
        alerts_detail=get_enum_url_parameter("alerts_detail", views.AlertsDetail),
    )
