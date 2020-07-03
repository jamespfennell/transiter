"""
Agencies

Endpoints for getting data on transit system agencies in a system.
"""
import flask

from transiter.http.httpmanager import (
    http_endpoint,
    link_target,
    get_enum_url_parameter,
)
from transiter.services import agencyservice, views

agency_endpoints = flask.Blueprint(__name__, __name__)


@http_endpoint(agency_endpoints, "")
@link_target(views.AgenciesInSystem, ["_system_id"])
def list_all_in_system(system_id):
    """
    List agencies in a system
    """
    return agencyservice.list_all_in_system(
        system_id,
        alerts_detail=get_enum_url_parameter("alerts_detail", views.AlertsDetail),
    )


@http_endpoint(agency_endpoints, "/<agency_id>")
@link_target(views.Agency, ["_system_id", "id"])
def get_in_system_by_id(system_id, agency_id):
    """
    Get an agency in a system
    """
    return agencyservice.get_in_system_by_id(
        system_id,
        agency_id,
        alerts_detail=get_enum_url_parameter("alerts_detail", views.AlertsDetail),
    )
