import flask

from transiter.http import permissions
from transiter.http.responsemanager import http_get_response, http_delete_response, http_put_response
from transiter.services import systemservice

system_endpoints = flask.Blueprint('system_endpoints', __name__)


@system_endpoints.route('')
@http_get_response
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


@system_endpoints.route('/<system_id>', methods=['GET'])
@http_get_response
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


@system_endpoints.route('/<system_id>', methods=['PUT'])
@http_put_response
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
    permissions.ensure(permissions.PermissionsLevel.ALL)
    config_str = flask.request.files['config_file'].read().decode('utf-8')
    extra_files = {
        key: flask.request.files[key].stream for key in flask.request.files
    }
    del extra_files['config_file']
    return systemservice.install(
        system_id=system_id,
        config_str=config_str,
        extra_files=extra_files,
        extra_settings=flask.request.form.to_dict()
    )


@system_endpoints.route('/<system_id>', methods=['DELETE'])
@http_delete_response
def delete_by_id(system_id):
    """Uninstall a system.

    .. :quickref: System; Uninstall a system

    :param system_id: The system's ID
    :status 204: the system was uninstalled
    :status 404: a system with that ID does not exists
    """
    permissions.ensure(permissions.PermissionsLevel.ALL)
    return systemservice.delete_by_id(system_id)
