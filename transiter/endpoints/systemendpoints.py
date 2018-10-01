from flask import Blueprint
from ..services import systemservice
from .responsemanager import http_get_response, http_delete_response, http_put_response

system_endpoints = Blueprint('system_endpoints', __name__)


@system_endpoints.route('/')
@http_get_response
def list_all():
    """List all systems

    .. :quickref: System; List all systems

    :status 200:
    :return: A JSON response like the following:

    .. code-block:: json

        [
            {
                "system_id": "nycsubway",
                "href": "https://transiter.io/systems/nycsubway"
            },
        ]

    """
    return systemservice.list_all()


@system_endpoints.route('/<system_id>/', methods=['GET'])
@http_get_response
def get_by_id(system_id):
    """Retrieve a specific system

    .. :quickref: System; Retrieve a specific system

    :param system_id: The system's ID
    :status 200: the system was found
    :status 404: a system with that ID does not exist
    :return: If successful, a JSON response like the following:

    .. code-block:: json

        {
            "system_id": "nycsubway",
            "stops": {
                "count": 40,
                "href": "https://transiter.io/systems/nycsubway/stops"
            },
            "stations": {
                "count": 33,
                "href": "(not implemented yet)"
            },
            "routes": {
                "count": 17,
                "href": "https://transiter.io/systems/nycsubway/routes"
            },
            "trips": {
                "count": 300,
                "href": "https://transiter.io/systems/nycsubway/trips"
            }
        }

    """
    return systemservice.get_by_id(system_id)


@system_endpoints.route('/<system_id>/', methods=['PUT'])
@http_put_response
def install(system_id):
    """Install a system

    .. :quickref: System; Install a system

    The data for the system to install (GTFS static data, feed data etc.)
    must already be on disk before the resource is created.

    :param system_id: The system's ID
    :status 200: the system's data was found on disk and the system was installed
    :status 404: data for such a system was not found
    """
    return systemservice.install(system_id)


@system_endpoints.route('/<system_id>/', methods=['DELETE'])
@http_delete_response
def delete_by_id(system_id):
    """Uninstall a system

    .. :quickref: System; Delete a system

    :param system_id: The system's ID
    :status 200: the system was uninstalled
    :status 404: a system with that ID does not exists
    """
    return systemservice.delete_by_id(system_id)
