from flask import Blueprint

from ..services import stopservice
from .responsemanager import http_get_response

stop_endpoints = Blueprint('stop_endpoints', __name__)


@stop_endpoints.route('/')
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
                "stop_id": "F01",
                "name": "14th st",
                "location": "Brooklyn",
                "usual_service": ["4", "5", "6"],
                "href": "https://transiter.io/systems/nycsubway/stops/F01"
            },
        ]

    """
    return stopservice.list_all_in_system(system_id)


@stop_endpoints.route('/<stop_id>/')
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
            "stop_id" : "L03",
            "location": "Brooklyn",
            "href": "(not implemented yet)",
            "usual_service": ['L'],
            "direction_names" : ["West Side (8 Av)", "East Side and Brooklyn"],
            "stop_events" : [
                {
                    "direction_name": "West Side (8 Av)",
                    "trip": {
                        "trip_id" : "LN1537314780",
                        "direction": "NI",
                        "status": "RUNNING",
                        "start_time" : 1537316340,
                        "last_update_time" : 1537316340,
                        "feed_update_time" : 1537316640,
                        "route": {
                            "route_id" : "L",
                            "href": "https://transiter.io/systems/nycsubway/routes/L"
                        },
                        "origin" : "NI",
                        "terminus" : "NI",
                        "href": "https://transiter.io/systems/nycsubway/trips/LN1537314780",
                    },
                    "arrival_time" : 1537316801,
                    "departure_time" : 1537316816,
                    "track" : "2",
                    "sequence_index" : 22,
                    "status": "FUTURE"
                },
            ],
            "parent_station": {
                "station_id" : 602,
                "name": "NI",
                "system": "NI",
                "location" : "Manhattan",
                "href": "(not implemented yet)",
                "child_stops" : [
                    {
                        "stop_id" : "635",
                        "name": "14th st",
                        'location' : 'NI',
                        "daytime_routes": ["4", "5", "6"],
                        "href": "https://transiter.io/systems/nycsubway/stops/602"
                    },
                ],
                "child_stations": [],
                "parent_station": null
            }
        }
    """
    return stopservice.get_in_system_by_id(system_id, stop_id)
