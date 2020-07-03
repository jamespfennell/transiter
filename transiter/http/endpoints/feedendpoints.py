"""
Feeds

Endpoints for getting information on feeds and for triggering feed updates.
"""

import flask
from flask import Blueprint

from transiter.http.httpmanager import (
    http_endpoint,
    link_target,
    HttpMethod,
    HttpStatus,
    is_sync_request,
)
from transiter import exceptions
from transiter.http.permissions import requires_permissions, PermissionsLevel
from transiter.services import feedservice, views

feed_endpoints = Blueprint(__name__, __name__)


@http_endpoint(feed_endpoints, "")
@link_target(views.FeedsInSystem, ["_system_id"])
@requires_permissions(PermissionsLevel.ADMIN_READ)
def list_all_in_system(system_id):
    """
    List feeds in a system

    List all the feeds in a transit system.

    Return code     | Description
    ----------------|-------------
    `200 OK`        | Returned if the system with this ID exists.
    `404 NOT FOUND` | Returned if no system with the provided ID is installed.
    """
    return feedservice.list_all_in_system(system_id)


@http_endpoint(feed_endpoints, "/<feed_id>")
@link_target(views.Feed, ["_system_id", "id"])
@requires_permissions(PermissionsLevel.ADMIN_READ)
def get_in_system_by_id(system_id, feed_id):
    """
    Get a feed in a system

    Describe a feed in a transit system.

    Return code         | Description
    --------------------|-------------
    `200 OK`            | Returned if the system and feed exist.
    `404 NOT FOUND`     | Returned if either the system or the feed does not exist.
    """
    return feedservice.get_in_system_by_id(system_id, feed_id)


@http_endpoint(feed_endpoints, "/<feed_id>", method=HttpMethod.POST)
@requires_permissions(PermissionsLevel.ALL)
def create_feed_update(system_id, feed_id):
    """
    Perform a feed update

    Perform a feed update of the given feed.
    The response is a description of the feed update.

    This endpoint is provided for one-off feed updates and development work.
    In general feed updates should instead be scheduled periodically using the transit system configuration;
    see the [transit system documentation](systems.md) for more information.

    Return code         | Description
    --------------------|-------------
    `201 CREATED`       | Returned if the system and feed exist, in which case the update is _scheduled_ (and executed in the same thread, if sync).
    `404 NOT FOUND`     | Returned if either the system or the feed does not exist.
    """
    user_provided_content = flask.request.files.get("content")
    if user_provided_content is not None:
        user_provided_content = user_provided_content.read()
        if len(user_provided_content) == 0:
            raise exceptions.InvalidInput("No file or an empty file provided.")
        if not is_sync_request():
            raise exceptions.InvalidInput(
                "Feed updates with content provided must be run synchronously. "
                "Use the sync=true url parameter."
            )
    feed_update_pk = feedservice.create_and_execute_feed_update(
        system_id,
        feed_id,
        execute_async=not is_sync_request(),
        content=user_provided_content,
    )
    return (
        feedservice.get_update_in_feed_by_pk(system_id, feed_id, feed_update_pk),
        HttpStatus.CREATED,
    )


@http_endpoint(feed_endpoints, "/<feed_id>/flush", method=HttpMethod.POST)
@requires_permissions(PermissionsLevel.ALL)
def create_feed_update_flush(system_id, feed_id):
    """
    Perform a feed flush

    The feed flush operation removes all entities from Transiter
    that were added through updates for the given feed.
    The operation is useful for removing stale data from the database.

    Return code         | Description
    --------------------|-------------
    `201 CREATED`       | Returned if the system and feed exist, in which case the flush is _scheduled_ (and executed in the same thread, if sync).
    `404 NOT FOUND`     | Returned if either the system or the feed does not exist.
    """
    feed_update_pk = feedservice.create_and_execute_feed_flush(
        system_id, feed_id, execute_async=not is_sync_request()
    )
    return (
        feedservice.get_update_in_feed_by_pk(system_id, feed_id, feed_update_pk),
        HttpStatus.CREATED,
    )


@http_endpoint(feed_endpoints, "/<feed_id>/updates")
@link_target(views.UpdatesInFeedLink, ["_system_id", "_feed_id"])
@requires_permissions(PermissionsLevel.ADMIN_READ)
def list_updates_in_feed(system_id, feed_id):
    """
    List updates for a feed

    List the most recent updates for a feed.
    Up to one hundred updates will be listed.

    Return code         | Description
    --------------------|-------------
    `200 OK`            | Returned if the system and feed exist.
    `404 NOT FOUND`     | Returned if either the system or the feed does not exist.
    """
    return feedservice.list_updates_in_feed(system_id, feed_id)
