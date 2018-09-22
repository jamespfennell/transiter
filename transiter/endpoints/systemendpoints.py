from flask import Blueprint
from ..services import systemservice

system_endpoints = Blueprint('system_endpoints', __name__)

@system_endpoints.route('/')
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

@system_endpoints.route('/<system_id>/')
def get(system_id):
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
    return 'System data (NI)\n'

@system_endpoints.route('/<system_id>/', methods=['PUT'])
def install(system_id):
    """Install a system

    .. :quickref: System; Install a system

    The data for the system to install (GTFS static data, feed data etc.)
    must already be on disk before the resource is created.

    :param system_id: The system's ID
    :status 200: the system's data was found on disk and the system was installed
    :status 404: data for such a system was not found
    """
    return 'Installing system (NI)\n'

@system_endpoints.route('/<system_id>/', methods=['DELETE'])
def delete(system_id):
    """Uninstall a system

    .. :quickref: System; Delete a system

    :param system_id: The system's ID
    :status 200: the system was uninstalled
    :status 404: a system with that ID does not exists
    """
    return 'Deleting system (NI)\n'
