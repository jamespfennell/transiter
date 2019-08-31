import flask
from transiter.http.httpmanager import http_endpoint, link_target, get_request_args
from transiter.services import stopservice, links

stop_endpoints = flask.Blueprint(__name__, __name__)


@http_endpoint(stop_endpoints, "")
@link_target(links.StopsInSystemIndexLink)
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


@http_endpoint(stop_endpoints, "/<stop_id>")
@link_target(links.StopEntityLink)
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
            "name": "Union Sq - 14 St",
            "service_maps": [
                {
                    "group_id": "realtime",
                    "routes": [
                        {
                            "id": "L"
                        }
                    ]
                },
            ],
            "direction_names": [
                "East Side and Brooklyn",
                "West Side (8 Av)"
            ],
            "stop_times": [
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
                        },
                        "last_stop": {
                            "id": "L29S",
                            "name": "Canarsie - Rockaway Pkwy"
                        },
                    }
                }
            ],
            "child_stops": [
                {
                    "id": "L03S",
                    "name": "Union Sq - 14 St",
                    "child_stops": []
                },
            ],
            "parent_stop": {
                "id": "635-L03-R20",
                "name": "14 St - Union Sq",
                "child_stops": [
                    {
                        "id": "R20",
                        "name": "14 St - Union Sq"
                    },
                ],
                "parent_stop": null
            }
        }

    """
    request_args = get_request_args(["earliest_time", "latest_time"])
    return stopservice.get_in_system_by_id(system_id, stop_id, **request_args)
