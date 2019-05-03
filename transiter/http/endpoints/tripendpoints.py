import flask

from transiter.http.httpmanager import link_target, http_endpoint
from transiter.services import tripservice, links

trip_endpoints = flask.Blueprint(__name__, __name__)


@http_endpoint(trip_endpoints, "")
def list_all_in_route(system_id, route_id):
    """List all trips for a specific system

    .. :quickref: Trip; List all trips for a specific system

    :param system_id: The system's ID
    :param route_id: The route's ID
    :status 200: the system was found
    :status 404: a system with that ID does not exist
    :return: If successful, a JSON response like the following:

    .. code-block:: json

        [
            {
                "id" : "LN1548014340",
                "last_stop": {
                    "id": "L20",
                    "name": "Canarsie",
                }
            }
        ]

    """
    return tripservice.list_all_in_route(system_id, route_id)


@http_endpoint(trip_endpoints, "/<trip_id>")
@link_target(links.TripEntityLink)
def get_in_route_by_id(system_id, route_id, trip_id):
    """Retrieve a specific trip in a specific system.

    .. :quickref: Trip; Retrieve a specific trip

    In version 0.2 this will accept a bunch of GET parameters for
    customizing the precise trip events to return (direction,
    status, etc..)

    :param system_id:  The system's ID
    :param route_id: The route's ID
    :param trip_id: The trip's ID
    :status 200: the stop was found
    :status 404: a stop with that ID does not exist within
        a system with that ID
    :return: If successful, a JSON response like the following:

    .. code-block:: json

        {
            "id": "LN1548014340",
            "direction_id": false,
            "start_time": 1548014340,
            "last_update_time": 1548016342,
            "current_status": "STOPPED_AT",
            "current_stop_sequence": 22,
            "vehicle_id": "0L 1459 RPY/8AV",
            "route": {
                "id": "L",
            },
            "stop_times": [
                {
                    "arrival_time": 1548016371,
                    "departure_time": 1548016386,
                    "track": "2",
                    "future": true,
                    "stop": {
                        "id": "L02N",
                        "name": "6 Av",
                    }
                },
            ],
        }

    Note that the stop event item here is the same as the stop event
    in a stop response, except stop data is returned instead of
    trip data.
    """
    return tripservice.get_in_route_by_id(system_id, route_id, trip_id)
