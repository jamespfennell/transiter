from flask import Blueprint

from transiter.services import routeservice
from transiter.http.responsemanager import http_get_response

route_endpoints = Blueprint('route_endpoints', __name__)


@route_endpoints.route('')
@http_get_response
def list_all_in_system(system_id):
    """List all routes for a specific system

    .. :quickref: Route; List all routes for a specific system

    :param system_id: The system's ID
    :status 200: the system was found
    :status 404: a system with that ID does not exist
    :return: If successful, a JSON response like the following:

    .. code-block:: json

        [
            {
                "id": "F",
                "status" : "UNPLANNED_SERVICE_CHANGE"
            },
        ]

    """
    return routeservice.list_all_in_system(system_id)


@route_endpoints.route('/<route_id>')
@http_get_response
def get_in_system_by_id(system_id, route_id):
    """Retrieve a specific route in a specific system

    .. :quickref: Route; Retrieve a specific route

    :param system_id:  The system's ID
    :param route_id: The route's ID
    :status 200: the route was found
    :status 404: a route with that ID does not exist within
        a system with that ID
    :return: If successful, a JSON response like the following:

    .. code-block:: json

        {
            "id": "A",
            "frequency": 6.7,
            "status": "GOOD_SERVICE",
            "alerts": [
                {
                    "id": "MTA NYCT_213185",
                    "message_title": "Track replacement",
                    "message_content": "10 PM Fri, Jan 18 to 5 AM Mon, Jan 21 Inwood-bound [A] trains make local stops at 23 St and 50 St in Manhattan",
                    "start_time": 1547787600,
                    "end_time": 1548046740,
                    "creation_time": 1547787600
                }
            ],
            "service_maps": [
                {
                    "group_id": "daytime",
                    "stops": [
                        {
                            "id": "A02",
                            "name": "Inwood - 207 St"
                        }
                    ]
                },
            ]
        }

    """
    return routeservice.get_in_system_by_id(system_id, route_id)
