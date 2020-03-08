import flask
import requests

from transiter import exceptions
from transiter.http import httpmanager
from transiter.http.httpmanager import (
    http_endpoint,
    link_target,
    HttpMethod,
    HttpStatus,
)
from transiter.http.permissions import requires_permissions, PermissionsLevel
from transiter.services import systemservice, links

system_endpoints = flask.Blueprint(__name__, __name__)


@http_endpoint(system_endpoints, "")
@link_target(links.SystemsIndexLink)
def list_all():
    """List all systems"""
    return systemservice.list_all()


@http_endpoint(system_endpoints, "/<system_id>")
@link_target(links.SystemEntityLink)
def get_by_id(system_id):
    """Get data on a specific system."""
    return systemservice.get_by_id(system_id)


@http_endpoint(
    system_endpoints, "/<system_id>", method=HttpMethod.PUT,
)
@requires_permissions(PermissionsLevel.ALL)
def install(system_id):
    """Install a system."""
    form_key_to_value = flask.request.form.to_dict()
    form_key_to_file_storage = flask.request.files.to_dict()

    if "config_file" in form_key_to_value:
        config_file_location = form_key_to_value["config_file"]
        try:
            response = requests.get(config_file_location)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            raise exceptions.InvalidInput(
                "Could not download YAML config file from '{}'".format(
                    config_file_location
                )
            )
        config_str = response.text
        del form_key_to_value["config_file"]
    elif "config_file" in form_key_to_file_storage:
        config_str = flask.request.files["config_file"].read().decode("utf-8")
    else:
        raise exceptions.InvalidInput("YAML config file not provided!")

    sync = httpmanager.is_sync_request()
    if sync:
        install_method = systemservice.install
    else:
        install_method = systemservice.install_async
    response = install_method(
        system_id=system_id, config_str=config_str, extra_settings=form_key_to_value,
    )

    # This means the system already exists and nothing was done.
    if not response:
        status = HttpStatus.OK
    else:
        if sync:
            status = HttpStatus.CREATED
        else:
            status = HttpStatus.ACCEPTED
    return systemservice.get_by_id(system_id), status


@http_endpoint(
    system_endpoints,
    "/<system_id>",
    method=HttpMethod.DELETE,
    returns_json_response=False,
)
@requires_permissions(PermissionsLevel.ALL)
def delete_by_id(system_id):
    """Uninstall a system."""
    systemservice.delete_by_id(
        system_id, error_if_not_exists=True, sync=httpmanager.is_sync_request()
    )
    return flask.Response(response="", status=HttpStatus.NO_CONTENT, content_type="")
