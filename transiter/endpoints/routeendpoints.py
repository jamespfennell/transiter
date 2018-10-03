from flask import Blueprint

from ..services import routeservice
from .responsemanager import http_get_response

route_endpoints = Blueprint('route_endpoints', __name__)


@route_endpoints.route('/')
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
                "route_id": "F",
                "service_status" : "Planned Work",
                "href": "https://transiter.io/systems/nycsubway/routes/F"
            },
        ]

    """
    return routeservice.list_all_in_system(system_id)


@route_endpoints.route('/<route_id>/')
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
            "route_id" : "F",
            "frequency" : 6,
            "service_status" : "Planned Work",
            "service_status_messages" : [
                {
                    "message_heading" : "Planned Work: Track Maintenance",
                    "posted_time" : 136266526,
                    "message_text" : "Downtown [B] [D] [F] [M] trains run at a slower speed."
                }
            ],
            "stops" : [
                {
                    "index" : 0,
                    "stop_id" : "F01",
                    "current_service" : true,
                    "borough" : "Queens",
                    "name": "Jamaica - 179 St",
                    "href": "https://transiter.io/systems/nycsubway/stops/F01"
                },
            ]
        }
    """
    return routeservice.get_in_system_by_id(system_id, route_id)
