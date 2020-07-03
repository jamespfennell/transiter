"""
Systems

Endpoints for installing, reading, configuring and deleting transit systems.
"""
import flask
import requests

from transiter import exceptions
from transiter.http import httpmanager, httpviews
from transiter.http.httpmanager import (
    http_endpoint,
    link_target,
    HttpMethod,
    HttpStatus,
)
from transiter.http.permissions import requires_permissions, PermissionsLevel
from transiter.services import stopservice, systemservice, views

system_endpoints = flask.Blueprint(__name__, __name__)


@http_endpoint(system_endpoints, "")
@link_target(httpviews.SystemsInstalled)
def list_all():
    """
    List all systems

    List all transit systems that are installed in this Transiter instance.
    """
    return systemservice.list_all()


@http_endpoint(system_endpoints, "/<system_id>")
@link_target(views.System, ["id"])
def get_by_id(system_id):
    """
    Get a specific system

    Get a system by its ID.

    Return code | Description
    ------------|-------------
    `200 OK` | A system with this ID exists.
    `404 NOT FOUND` | No system with the provided ID is installed.
    """
    return systemservice.get_by_id(system_id)


@http_endpoint(system_endpoints, "/<system_id>/transfers")
@link_target(views.TransfersInSystem, ["_system_id"])
def list_all_transfers_in_system(system_id):
    """
    List all transfers in a system

    List all transfers in a system.

    Return code | Description
    ------------|-------------
    `200 OK` | A system with this ID exists.
    `404 NOT FOUND` | No system with the provided ID is installed.
    """
    from_stop_ids = httpmanager.get_list_url_parameter("from_stop_id")
    to_stop_ids = httpmanager.get_list_url_parameter("to_stop_id")
    return stopservice.list_all_transfers_in_system(
        system_id, from_stop_ids=from_stop_ids, to_stop_ids=to_stop_ids
    )


@http_endpoint(
    system_endpoints, "/<system_id>", method=HttpMethod.PUT,
)
@requires_permissions(PermissionsLevel.ALL)
def install(system_id):
    """
    Install a system

    This endpoint is used to install or update transit systems.
    Installs/updates can be performed asynchronously (recommended)
    or synchronously (using the optional URL parameter `sync=true`; not recommended);
    see below for more information.

    The endpoint accepts `multipart/form-data` requests.
    There is a single required parameter, `config_file`, which
    specifies the YAML configuration file for the Transit system.
    (There is a [dedicated documentation page](systems.md) concerned with creating transit system configuration files.)
    The parameter can either be:

    - A file upload of the configuration file, or
    - A text string, which will be interpreted as a URL pointing to the configuration file.

    In addition, depending on the configuration file, the endpoint will also accept extra text form data parameters.
    These additional parameters are used for things like API keys, which are different
    for each user installing the transit system.
    The configuration file will customize certain information using the parameters -
        for example, it might include an API key as a GET parameter in a feed URL.
    If you are installing a system using a YAML configuration provided by someone else, you
     should be advised of which additional parameters are needed.
    If you attempt to install a system without the required parameters, the install will fail and
    the response will detail which parameters you're missing.

    #### Async versus sync

    Often the install/update process is long because it often involves performing
    large feed updates
    of static feeds - for example, in the case of the New York City Subway,
    an install takes close to two minutes.
    If you perform a synchronous install, the install request is liable
    to timeout - for example, Gunicorn by default terminates HTTP
    requests that take over 60 seconds.
    For this reason you should generally install asynchronously.

    After triggering the install asynchronously, you can track its
    progress by hitting the `GET` system endpoint repeatedly.

    Synchronous installs are supported and useful when writing new
    transit system configs, in which case getting feedback from a single request
    is quicker.

    Return code         | Description
    --------------------|-------------
    `201 CREATED`       | For synchronous installs, returned if the transit system was successfully installed.
    `202 ACCEPTED`      | For asynchronous installs, returned if the install is successfully triggered. This does not necessarily mean the system will be succesfully installed.
    `400 BAD REQUEST`   | Returned if the YAML configuration file cannot be retrieved. For synchronous installs, this code is also returned if there is any kind of install error.
    """
    form_key_to_value = flask.request.form.to_dict()
    config_file_url = form_key_to_value.pop("config_file", None)

    sync = httpmanager.is_sync_request()
    system_update_pk = systemservice.install(
        system_id=system_id,
        config_str=_get_config_file(
            config_file_url, flask.request.files.get("config_file")
        ),
        extra_settings=form_key_to_value,
        config_source_url=config_file_url,
        sync=sync,
    )

    if sync:
        if (
            systemservice.get_update_by_id(system_update_pk).status
            == views.SystemUpdateStatus.SUCCESS
        ):
            status = HttpStatus.CREATED
        else:
            status = HttpStatus.BAD_REQUEST
    else:
        status = HttpStatus.ACCEPTED
    return systemservice.get_update_by_id(system_update_pk), status


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
    """
    Uninstall (delete) a system

    The uninstall can be performed asynchronously or synchronously (using the
    optional URL parameter `sync=true`).

    You should almost always use the asynchronous version of this endpoint.
    It works by changing the system ID to be a new "random" ID, and then performs
    the delete asynchronously.
    This means that at soon as the HTTP request ends (within a few milliseconds)
    the system is invisible to users, and available for installing a new system.

    The actual delete takes up to a few minutes for large transit systems like
    the NYC Subway.

    Return code         | Description
    --------------------|-------------
    `202 ACCEPTED`      | For asynchronous deletes, returned if the delete is successfully triggered.
    `204 NO CONTENT`    | For synchronous deletes, returned if the system was successfully deleted.
    `404 NOT FOUND`     | Returned if the system does not exist.

    """
    systemservice.delete_by_id(
        system_id, error_if_not_exists=True, sync=httpmanager.is_sync_request()
    )
    if httpmanager.is_sync_request():
        status = HttpStatus.NO_CONTENT
    else:
        status = HttpStatus.ACCEPTED
    return flask.Response(response="", status=status, content_type="")


@http_endpoint(
    system_endpoints, "/<system_id>/auto-update", method=HttpMethod.PUT,
)
@requires_permissions(PermissionsLevel.ALL)
def set_auto_update_enabled(system_id):
    """
    Configure system auto-update

    Configure whether auto-update is enabled for
     auto-updatable feeds in a system.

    The endpoint takes a single form parameter `enabled`
    which can either be `true` or `false` (case insensitive).

    Return code         | Description
    --------------------|-------------
    `204 NO CONTENT`    | The configuration was applied successfully.
    `400 BAD REQUEST`   | Returned if the form parameter is not provided or is invalid.
    `404 NOT FOUND`     | Returned if the system does not exist.
    """
    # TODO: this should just accept a URL parameter
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
