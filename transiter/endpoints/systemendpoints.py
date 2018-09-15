from flask import Blueprint
from ..services import systemservice

system_endpoints = Blueprint('system_endpoints', __name__)

@system_endpoints.route('/')
def list_all():
    return systemservice.list_all()

@system_endpoints.route('/<system_id>/')
def get(system_id):
    return 'System data (NI)\n'

@system_endpoints.route('/<system_id>/', methods=['PUT'])
def install(system_id):
    return 'Installing system (NI)\n'

@system_endpoints.route('/<system_id>/', methods=['DELETE'])
def delete(system_id):
    return 'Deleting system (NI)\n'
