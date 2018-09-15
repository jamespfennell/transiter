from flask import Blueprint
from ..services import systemservice

feed_endpoints = Blueprint('feed_endpoints', __name__)

@feed_endpoints.route('/')
def list_all(system_id):
    return feedservice.list_all()

@feed_endpoints.route('/<feed_id>/')
def get(system_id, feed_id):
    return 'Feed data (NI)\n'

@feed_endpoints.route('/<feed_id>/', methods=['POST'])
def update(system_id, feed_id):
    return 'Updating feed \n'
