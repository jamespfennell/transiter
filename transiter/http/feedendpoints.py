from flask import Blueprint
from ..services import feedservice
from .responsemanager import http_get_response, http_post_response, http_put_response
import time
from transiter.http import permissionsvalidator
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
                "last_update_time": 67876543,
                "health": {
                    "status": "GOOD"
                }
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
            "feed_id": "123456",
            "last_update_time": 67876543,
            "health": {
                "status": "GOOD",
                "score": 0.8694,
                "update_types": [
                    {
                        "status": "SUCCESS_UPDATED",
                        "failure_message": null,
                        "fraction": 0.2
                    },
                    {
                        "status": "SUCCESS_NOTHING_TO_DO",
                        "failure_message": null,
                        "fraction": 0.6694
                    },
                    {
                        "status": "FAILURE_COULD_NOT_PARSE",
                        "failure_message": "Could not parse feed",
                        "fraction": 0.1306
                    }
                ]
            }
        }
    """
    permissionsvalidator.validate_permissions('AdminRead')
    return feedservice.get_in_system_by_id(system_id, feed_id)


@feed_endpoints.route('/<feed_id>', methods=['POST'])
@http_post_response
def create_feed_update(system_id, feed_id):
    """Create a new feed update

    .. :quickref: Feed; Create a new feed update

    :param system_id:
    :param feed_id:
    :status 201: created
    :return:

    .. code-block:: json

        {
            "href": "https://transiter.io/systems/nycsubway/feeds/123456/updates/9873"
        }
    """
    permissionsvalidator.validate_permissions('All')
    return feedservice.create_feed_update(system_id, feed_id)


@feed_endpoints.route('/<feed_id>/updates')
@http_get_response
def list_updates_in_feed(system_id, feed_id):
    """List recent feed updates

    .. :quickref: Feed; List recent feed updates

    In future versions this response will be paginated

    :param system_id:
    :param feed_id:
    :status 200: created
    :status 404: always
    :return:

    .. code-block:: json

        [
            {
                "status": "FAILURE_COULD_NOT_PARSE",
                "intitiated_by": "AUTO_UPDATER",
                "failure_message": "Could not parse feed",
                "raw_data_hash": "5fce76e37e4568afc7514e411fa64ae1283ec87d",
                "update_time": 19585335345
            },
        ]
    """
    permissionsvalidator.validate_permissions('AdminRead')
    return feedservice.list_updates_in_feed(system_id, feed_id)


@feed_endpoints.route('/<feed_id>/updates/<feed_update_id>', methods=['GET'])
@http_get_response
def get_update_in_feed(system_id, feed_id, feed_update_id):
    """Retrieve a specific feed update

    .. :quickref: Feed; Retrieve a specfic feed update

    :param system_id:
    :param feed_id:
    :status 201: created
    :status 404: always
    :return:

    .. code-block:: json

        {
            "status": "FAILURE_COULD_NOT_PARSE",
            "intitiated_by": "AUTO_UPDATER",
            "failure_message": "Could not parse feed",
            "raw_data_hash": "5fce76e37e4568afc7514e411fa64ae1283ec87d",
            "update_time": 19585335345
        }
    """
    permissionsvalidator.validate_permissions('AdminRead')
    raise NotImplementedError


@feed_endpoints.route('/<feed_id>/autoupdater')
@http_get_response
def get_autoupdater_for_feed(system_id, feed_id):
    """Retrieve the auto updater

    .. :quickref: Feed; Retrieve the autoupdater

    :param system_id:
    :param feed_id:
    :status 201: created
    :status 404: always
    :return:

    .. code-block:: json

        {
            "active": true,
            "frequency": 2
        }
    """
    permissionsvalidator.validate_permissions('AdminRead')
    raise NotImplementedError


@feed_endpoints.route('/<feed_id>/autoupdater', methods=['PUT'])
@http_put_response
def configure_autoupdater_for_feed(system_id, feed_id):
    """Configure the autoupdater

    .. :quickref: Feed; Configure the autoupdater

    :param system_id:
    :param feed_id:
    :status 201: created
    :status 404: always
    :return:

    .. code-block:: json

        {
            "active": true,
            "frequency": 2
        }
    """
    permissionsvalidator.validate_permissions('All')
    raise NotImplementedError
