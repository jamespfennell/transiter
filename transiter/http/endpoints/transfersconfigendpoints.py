import flask

from transiter.http.httpmanager import (
    http_endpoint,
    HttpMethod,
    link_target,
    get_float_url_parameter,
    get_list_url_parameter,
)
from transiter.services import transfersconfigservice, views

transfers_config_endpoints = flask.Blueprint(__name__, __name__)


@http_endpoint(transfers_config_endpoints, "")
def list_all():
    return transfersconfigservice.list_all()


@http_endpoint(transfers_config_endpoints, "/preview", method=HttpMethod.POST)
def preview():
    return transfersconfigservice.preview(
        system_ids=get_list_url_parameter("system_id", required=True),
        distance=get_float_url_parameter("distance", required=True),
    )


@http_endpoint(transfers_config_endpoints, "", method=HttpMethod.POST)
def create():
    config_id = transfersconfigservice.create(
        system_ids=get_list_url_parameter("system_id", required=True),
        distance=get_float_url_parameter("distance", required=True),
    )
    return transfersconfigservice.get_by_id(config_id=config_id)


@http_endpoint(transfers_config_endpoints, "/<int:config_id>")
@link_target(views.TransfersConfig, ["id"])
def get_by_id(config_id):
    return transfersconfigservice.get_by_id(config_id=config_id)


@http_endpoint(transfers_config_endpoints, "/<int:config_id>", method=HttpMethod.PUT)
def update(config_id):
    transfersconfigservice.update(
        config_id=config_id,
        system_ids=get_list_url_parameter("system_id", required=True),
        distance=get_float_url_parameter("distance", required=True),
    )
    return transfersconfigservice.get_by_id(config_id=config_id)


@http_endpoint(transfers_config_endpoints, "/<int:config_id>", method=HttpMethod.DELETE)
def delete(config_id):
    return transfersconfigservice.delete(config_id=config_id)
