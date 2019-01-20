from flask import Blueprint

from transiter.http import permissionsvalidator
from transiter.http.responsemanager import http_get_response, http_post_response
from transiter.services import feedservice

feed_endpoints = Blueprint('feed_endpoints', __name__)


@feed_endpoints.route('')
@http_get_response
def list_all_in_system(system_id):
    """List all feeds for a specific system


    .. :quickref: Feed; List all feeds for a specific system

    :param system_id:
    :return:

    .. code-block:: json

        [
            {
                "feed_id": "123456",
                "href": "https://transiter.io/systems/nycsubway/feeds/123456",
            },
        ]
    """
    permissionsvalidator.validate_permissions('AdminRead')
    return feedservice.list_all_in_system(system_id)


@feed_endpoints.route('/<feed_id>')
@http_get_response
def get_in_system_by_id(system_id, feed_id):
    """Retrieve a specific feed


    .. :quickref: Feed; Retrieve a specific feed

    :param system_id:
    :param feed_id:
    :return:

    .. code-block:: json

        {
            "id": "L",
            "updates": {
                "href": "https://demo.transitor.io/systems/nycsubway/feeds/L/updates"
            }
        }
    """
    permissionsvalidator.validate_permissions('AdminRead')
    return feedservice.get_in_system_by_id(system_id, feed_id)


@feed_endpoints.route('/<feed_id>', methods=['POST'])
@http_post_response
def create_feed_update(system_id, feed_id):
    """Create a new feed update.

    The response is identical to the feed update's response in thelist
    updates reference

    .. :quickref: Feed; Create a new feed update

    :param system_id:
    :param feed_id:
    :status 201: created
    :status 404: if the feed could not be found
    :return:

    .. code-block:: json

        {
            "id": 6,
            "status": "SUCCESS",
            "explanation": "UPDATED",
            "raw_data_hash": "099ae3c5b72d6f2d8fc6eb4290a95776",
            "last_action_time": 1548014018.17677
        }
    """
    permissionsvalidator.validate_permissions('All')
    return feedservice.create_feed_update(system_id, feed_id)


@feed_endpoints.route('/<feed_id>/updates')
@http_get_response
def list_updates_in_feed(system_id, feed_id):
    """List recent feed updates.

    The status can be either SUCCESS or FAILURE. The explanation is a further
    code for why the status is such.

    .. :quickref: Feed; List recent feed updates

    In future versions this response will be paginated

    :param system_id:
    :param feed_id:
    :status 200: if the feed exists
    :status 404: if the feed does not exist
    :return:

    .. code-block:: json

        [
            {
                "id": 3,
                "status": "SUCCESS",
                "explanation": "NOT_NEEDED",
                "raw_data_hash": "dd1c428955aad6fb17712ec1e6449ba1",
                "last_action_time": 1548013683.83237
            },
            {
                "id": 2,
                "status": "SUCCESS",
                "explanation": "UPDATED",
                "raw_data_hash": "dd1c428955aad6fb17712ec1e6449ba1",
                "last_action_time": 1548013682.624686
            }
        ]
    """
    permissionsvalidator.validate_permissions('AdminRead')
    return feedservice.list_updates_in_feed(system_id, feed_id)

