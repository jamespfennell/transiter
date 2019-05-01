from flask import Blueprint

from transiter.http.httpmanager import http_endpoint, RequestType, link_target
from transiter.http.permissions import requires_permissions, PermissionsLevel
from transiter.services import feedservice, links

feed_endpoints = Blueprint(__name__, __name__)


@http_endpoint(feed_endpoints, "")
@link_target(links.FeedsInSystemIndexLink)
@requires_permissions(PermissionsLevel.ADMIN_READ)
def list_all_in_system(system_id):
    """List all feeds for a specific system

    .. :quickref: Feed; List all feeds for a specific system

    :param system_id:
    :return:

    .. code-block:: json

        [
            {
                "id": "123456",
            },
        ]
    """
    return feedservice.list_all_in_system(system_id)


@http_endpoint(feed_endpoints, "/<feed_id>")
@link_target(links.FeedEntityLink)
@requires_permissions(PermissionsLevel.ADMIN_READ)
def get_in_system_by_id(system_id, feed_id):
    """Retrieve a specific feed

    .. :quickref: Feed; Retrieve a specific feed

    :param system_id:
    :param feed_id:
    :return:

    .. code-block:: json

        {
            "id": "L",
        }
    """
    return feedservice.get_in_system_by_id(system_id, feed_id)


@http_endpoint(feed_endpoints, "/<feed_id>", RequestType.UPDATE)
@requires_permissions(PermissionsLevel.ALL)
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
            "failure_message": null,
            "raw_data_hash": "099ae3c5b72d6f2d8fc6eb4290a95776",
            "last_action_time": 1548014018
        }
    """
    return feedservice.create_feed_update(system_id, feed_id)


@http_endpoint(feed_endpoints, "/<feed_id>/updates")
@requires_permissions(PermissionsLevel.ADMIN_READ)
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
                "id": 7,
                "status": "SUCCESS",
                "explanation": "NOT_NEEDED",
                "failure_message": null,
                "raw_data_hash": "099ae3c5b72d6f2d8fc6eb4290a95776",
                "last_action_time": 1548014023
            },
            {
                "id": 6,
                "status": "SUCCESS",
                "explanation": "UPDATED",
                "failure_message": null,
                "raw_data_hash": "099ae3c5b72d6f2d8fc6eb4290a95776",
                "last_action_time": 1548014018
            }
        ]
    """
    return feedservice.list_updates_in_feed(system_id, feed_id)
