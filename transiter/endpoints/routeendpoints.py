from flask import Blueprint

from ..services import routeservice

route_endpoints = Blueprint('route_endpoints', __name__)


@route_endpoints.route('/')
def list_all(system_id):
    return routeservice.list_all(system_id)


@route_endpoints.route('/<route_id>/')
def get(system_id, route_id):
    """
    Sample doc
    :param system_id:  Hello
    :param route_id:  Me
    :return: asf
    """
    return routeservice.get(system_id, route_id)
