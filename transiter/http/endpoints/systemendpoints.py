import flask

from transiter.http.permissions import requires_permissions, PermissionsLevel
from transiter.http.httpmanager import http_endpoint, RequestType, link_target
from transiter.services import systemservice, links

system_endpoints = flask.Blueprint(__name__, __name__)


@http_endpoint(system_endpoints, "")
@link_target(links.SystemsIndexLink)
def list_all():
    """List all systems

    .. :quickref: System; List all systems.

    :status 200:
    :return: A JSON response like the following:

    .. code-block:: json

        [
            {
                "id": "nycsubway"
            },
        ]

    """
    return systemservice.list_all()


@http_endpoint(system_endpoints, "/<system_id>")
@link_target(links.SystemEntityLink)
def get_by_id(system_id):
    """Get data on a specific system.

    .. :quickref: System; Get a specific system

    :param system_id: The system's ID
    :status 200: the system was found
    :status 404: a system with that ID does not exist

    **Example JSON response**

    .. code-block:: json

        {
            "id": "nycsubway",
            "stops": {
                "count": 40
            },
            "routes": {
                "count": 17
            },
            "trips": {
                "count": 300
            }
        }

    """
    return systemservice.get_by_id(system_id)


@http_endpoint(system_endpoints, "/<system_id>", RequestType.CREATE)
@requires_permissions(PermissionsLevel.ALL)
def install(system_id):
    """Install a system.

    .. :quickref: System; Install a system.

    :param system_id: The system's ID

    :status 201: the system was installed
    :status 404: data for such a system was not found

    :formparameter config_file: the system's TOML config
    :formparameter (additional file name): additional file uploads
        (for example, direction name CSVs) required by the system config.
    :formparameter (additional setting name): additional settings (for example,
        API keys) required by the system config.
    """
    config_str = flask.request.files["config_file"].read().decode("utf-8")
    extra_files = {key: flask.request.files[key].stream for key in flask.request.files}
    del extra_files["config_file"]
    return systemservice.install(
        system_id=system_id,
        config_str=config_str,
        extra_files=extra_files,
        extra_settings=flask.request.form.to_dict(),
    )


@http_endpoint(system_endpoints, "/<system_id>", RequestType.DELETE)
@requires_permissions(PermissionsLevel.ALL)
def delete_by_id(system_id):
    """Uninstall a system.

    .. :quickref: System; Uninstall a system

    :param system_id: The system's ID
    :status 204: the system was uninstalled
    :status 404: a system with that ID does not exists
    """
    return systemservice.delete_by_id(system_id)
