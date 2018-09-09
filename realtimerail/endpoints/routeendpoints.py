from flask import Blueprint

from ..services import routeservice

route_endpoints = Blueprint('route_endpoints', __name__)

@route_endpoints.route('/')
def list_all(system_id):
    return routeservice.list_all(system_id)

@route_endpoints.route('/<route_id>/')
def get(system_id, route_id):
    return routeservice.get(system_id, route_id)
