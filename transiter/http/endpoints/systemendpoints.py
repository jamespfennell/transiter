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

    config_source_url = None
    if "config_file" in form_key_to_value:
        config_source_url = form_key_to_value["config_file"]
        try:
            response = requests.get(config_source_url)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            raise exceptions.InvalidInput(
                "Could not download YAML config file from '{}'".format(
                    config_source_url
                )
            )
        config_str = response.text
        del form_key_to_value["config_file"]
    elif "config_file" in form_key_to_file_storage:
        config_str = flask.request.files["config_file"].read().decode("utf-8")
    else:
        raise exceptions.InvalidInput("YAML config file not provided!")

    # TODO: replace with httpmanager.get_boolean_url_parameter("sync")
    sync = httpmanager.is_sync_request()
    response = systemservice.install(
        system_id=system_id,
        config_str=config_str,
        extra_settings=form_key_to_value,
        config_source_url=config_source_url,
        sync=sync,
    )

    # This means the system already exists and nothing was done.
    # TODO: this is all wrong
    if not response:
        status = HttpStatus.OK
    else:
        if sync:
            status = HttpStatus.CREATED
        else:
            status = HttpStatus.ACCEPTED
    # TODO return a representation of the update instead
    return systemservice.get_by_id(system_id), status


# TODO: use this method
def _get_config_file(config_source_url, uploaded_config_file):
    if config_source_url is not None:
        try:
            response = requests.get(config_source_url)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            raise exceptions.InvalidInput(
                "Could not download YAML config file from '{}'".format(
                    config_source_url
                )
            )
        return response.text
    elif uploaded_config_file is not None:
        return uploaded_config_file.read().decode("utf-8")
    else:
        raise exceptions.InvalidInput("YAML config file not provided!")


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


@http_endpoint(
    system_endpoints, "/<system_id>/auto-update", method=HttpMethod.PUT,
)
@requires_permissions(PermissionsLevel.ALL)
def set_auto_update_enabled(system_id):
    form_key_to_value = flask.request.form.to_dict()
    enabled = form_key_to_value.get("enabled")
    if enabled is None:
        raise exceptions.InvalidInput("The form variable 'enabled' is required")
    enabled = enabled.lower()
    if enabled not in {"false", "true"}:
        raise exceptions.InvalidInput(
            "The form variable 'enabled' has to be 'true' or 'false', not '{}'".format(
                enabled
            )
        )
    systemservice.set_auto_update_enabled(
        system_id, form_key_to_value["enabled"].lower() == "true"
    )
    return "", HttpStatus.NO_CONTENT
