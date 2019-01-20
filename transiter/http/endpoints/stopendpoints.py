from flask import Blueprint

from transiter.services import stopservice
from transiter.http.responsemanager import http_get_response

stop_endpoints = Blueprint('stop_endpoints', __name__)


@stop_endpoints.route('')
@http_get_response
def list_all_in_system(system_id):
    """List all stops for a specific system

    .. :quickref: Stop; List all stops for a specific system

    :param system_id: The system's ID
    :status 200: the system was found
    :status 404: a system with that ID does not exist
    :return: If successful, a JSON response like the following:

    .. code-block:: json

        [
            {
                "id": "F01",
                "name": "14th st",
                "system_id": "nycsubway",
                "href": "https://demo.transiter.io/systems/nycsubway/stops/F01"
            },
        ]

    """
    return stopservice.list_all_in_system(system_id)


@stop_endpoints.route('/<stop_id>')
@http_get_response
def get_in_system_by_id(system_id, stop_id):
    """Retrieve a specific stop in a specific system.

    .. :quickref: Stop; Retrieve a specific stop

    In version 0.2 this will accept a bunch of GET parameters for
    customizing the precise stop events to return.

    :param system_id:  The system's ID
    :param stop_id: The stop's ID
    :status 200: the stop was found
    :status 404: a stop with that ID does not exist within
        a system with that ID
    :return: If successful, a JSON response like the following:

    .. code-block:: json

        {
            "id": "L03",
            "system_id": "nycsubway",
            "name": "Union Sq - 14 St",
            "usual_routes": [
                {
                    "id": "L",
                    "system_id": "nycsubway",
                    "href": "https://demo.transiter.io/systems/nycsubway/routes/L"
                },
            ],
            "direction_names": [
                "East Side and Brooklyn",
                "West Side (8 Av)"
            ],
            "stop_events": [
                {
                    "stop_id": "L03S",
                    "direction_name": "East Side and Brooklyn",
                    "arrival_time": 1548015540,
                    "departure_time": 1548015555,
                    "track": "1",
                    "future": true,
                    "trip": {
                        "id": "LS1548015360",
                        "direction_id": true,
                        "start_time": 1548015360,
                        "last_update_time": 1548015502,
                        "current_status": "STOPPED_AT",
                        "current_stop_sequence": 2,
                        "vehicle_id": "0L 1516 8AV/RPY",
                        "route": {
                            "id": "L",
                            "system_id": "nycsubway",
                            "href": "https://demo.transiter.io/systems/nycsubway/routes/L"
                        },
                        "last_stop": {
                            "id": "L29S",
                            "system_id": "nycsubway",
                            "name": "Canarsie - Rockaway Pkwy"
                        },
                        "href": "https://demo.transiter.io/systems/nycsubway/routes/L/trips/LS1548015360"
                    }
                }
            ],
            "child_stops": [
                {
                    "id": "L03S",
                    "system_id": "nycsubway",
                    "name": "Union Sq - 14 St",
                    "usual_routes": [],
                    "href": "https://demo.transiter.io/systems/nycsubway/stops/L03S",
                    "child_stops": []
                },
            ],
            "parent_stop": {
                "id": "635-L03-R20",
                "system_id": "nycsubway",
                "name": "14 St - Union Sq",
                "usual_routes": [],
                "href": "https://demo.transiter.io/systems/nycsubway/stops/635-L03-R20",
                "child_stops": [
                    {
                        "id": "R20",
                        "system_id": "nycsubway",
                        "name": "14 St - Union Sq",
                        "usual_routes": [],
                        "href": "https://demo.transiter.io/systems/nycsubway/stops/R20"
                    },
                ],
                "parent_stop": null
            }
        }

    """
    return stopservice.get_in_system_by_id(system_id, stop_id)
