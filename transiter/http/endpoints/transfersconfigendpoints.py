"""
Inter-system transfers management

These endpoints are used to manage inter-system transfers using
*transfers config*.
A transfers config describes which transit systems Transiter should create
    transfers between, and how to determine which stops should have transfers between
    them.

As of version 0.5, Transiter supports a single mechanism for creating
    inter-system transfers: geographical proximity.
Given a collection of systems and a distance (always in meters),
    Transiter will create transfers for stops in distinct systems
    which are less than the given distance apart.
When creating a new config, it's best to start by using the preview endpoint
    to see what transfers would create using that config.
Then, when satisfied with the parameters, the config can be persisted using
    the create endpoint below.

"""

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
    """
    List all transfers configs

    List all of the transfers configs that are installed.
    """
    return transfersconfigservice.list_all()


@http_endpoint(transfers_config_endpoints, "/preview", method=HttpMethod.POST)
def preview():
    """
    Preview a transfers config

    This endpoint returns a preview of the transfers that would be created
    using a specific config.

    URL parameter | type | description
    --------------|------|------------
    `system_id`   | multiple string values | The system IDs to create transfers between
    `distance`    | float | the maximum distance, in meters, between two stops in order for a transfer to be created between them
    """
    return transfersconfigservice.preview(
        system_ids=get_list_url_parameter("system_id", required=True),
        distance=get_float_url_parameter("distance", required=True),
    )


@http_endpoint(transfers_config_endpoints, "", method=HttpMethod.POST)
def create():
    """
    Create a transfers config

    This endpoint is identical to the preview endpoint, except that the resulting
    transfers are persisted and a new transfer config is created.
    """
    config_id = transfersconfigservice.create(
        system_ids=get_list_url_parameter("system_id", required=True),
        distance=get_float_url_parameter("distance", required=True),
    )
    return transfersconfigservice.get_by_id(config_id=config_id)


@http_endpoint(transfers_config_endpoints, "/<int:config_id>")
@link_target(views.TransfersConfig, ["id"])
def get_by_id(config_id):
    """
    Get a transfers config
    """
    return transfersconfigservice.get_by_id(config_id=config_id)


@http_endpoint(transfers_config_endpoints, "/<int:config_id>", method=HttpMethod.PUT)
def update(config_id):
    """
    Update a transfers config

    This endpoint is identical to the preview endpoint, except that the resulting
    transfers are persisted and a new transfer config is created.
    """
    transfersconfigservice.update(
        config_id=config_id,
        system_ids=get_list_url_parameter("system_id", required=True),
        distance=get_float_url_parameter("distance", required=True),
    )
    return transfersconfigservice.get_by_id(config_id=config_id)


@http_endpoint(transfers_config_endpoints, "/<int:config_id>", method=HttpMethod.DELETE)
def delete(config_id):
    """
    Delete a transfers config

    This endpoint deletes the config as well as all transfers associated to the config.
    """
    return transfersconfigservice.delete(config_id=config_id)
