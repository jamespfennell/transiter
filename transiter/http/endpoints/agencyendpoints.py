import flask

from transiter.http.httpmanager import http_endpoint, link_target
from transiter.services import agencyservice, views

agency_endpoints = flask.Blueprint(__name__, __name__)


@http_endpoint(agency_endpoints, "")
@link_target(views.AgenciesInSystem, ["_system_id"])
def list_all_in_system(system_id):
    return agencyservice.list_all_in_system(system_id)


@http_endpoint(agency_endpoints, "/<agency_id>")
@link_target(views.Agency, ["_system_id", "id"])
def get_in_system_by_id(system_id, agency_id):
    return agencyservice.get_in_system_by_id(system_id, agency_id)
